from typing import Optional, List
import requests
from config import settings
from models.paper import Paper, SearchResult
from utils.cache import get_cache, set_cache


class SemanticScholarService:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self):
        self.timeout = settings.request_timeout
        self.api_key = settings.semantic_scholar_api_key

    def _headers(self) -> dict:
        headers = {"User-Agent": "ResearchCLI/1.0"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def search(self, query: str, year_range: Optional[str] = None,
               limit: int = 20, page: int = 1) -> SearchResult:
        cache_key = f"search_{query}_{year_range}_{limit}_{page}"
        cached = get_cache("semantic", cache_key)
        if cached:
            return SearchResult(**cached)

        fields = "title,authors,venue,year,citationCount,externalIds,abstract,openAccessPdf,publicationDate"
        params = {
            "query": query,
            "limit": min(limit, 100),
            "offset": (page - 1) * limit,
            "fields": fields,
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                timeout=self.timeout,
                headers=self._headers(),
            )

            if response.status_code == 403:
                params.pop("fields", None)
                response = requests.get(
                    f"{self.BASE_URL}/paper/search",
                    params={**params, "fields": "title,authors,venue,year,citationCount,externalIds"},
                    timeout=self.timeout,
                    headers=self._headers(),
                )

            response.raise_for_status()
            data = response.json()
            result = self._parse_search_response(data, query)
            set_cache("semantic", cache_key, result.model_dump())
            return result
        except requests.RequestException:
            return SearchResult(query=query, source="semantic_scholar", total_results=0)

    def fetch_by_doi(self, doi: str) -> Optional[Paper]:
        cache_key = f"doi_{doi}"
        cached = get_cache("semantic", cache_key)
        if cached:
            return Paper(**cached)

        fields = "title,authors,venue,year,citationCount,externalIds,abstract,openAccessPdf,references,publicationDate"
        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/DOI:{doi_clean}",
                params={"fields": fields},
                timeout=self.timeout,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
            paper = self._parse_paper(data)
            if paper:
                set_cache("semantic", cache_key, paper.model_dump())
            return paper
        except requests.RequestException:
            return None

    def fetch_related(self, doi: str, limit: int = 10) -> SearchResult:
        cache_key = f"related_{doi}_{limit}"
        cached = get_cache("semantic", cache_key)
        if cached:
            return SearchResult(**cached)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        fields = "title,authors,venue,year,citationCount,externalIds,abstract"
        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/DOI:{doi_clean}/citations",
                params={"fields": fields, "limit": limit},
                timeout=self.timeout,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
            papers = []
            for item in data.get("data", []):
                citing_paper = item.get("citingPaper", {})
                paper = self._parse_paper(citing_paper)
                if paper:
                    papers.append(paper)
            result = SearchResult(
                query=f"related_to_{doi}",
                total_results=len(papers),
                papers=papers,
                source="semantic_scholar",
            )
            set_cache("semantic", cache_key, result.model_dump())
            return result
        except requests.RequestException:
            return SearchResult(query=doi, source="semantic_scholar", total_results=0)

    def _parse_search_response(self, data: dict, query: str) -> SearchResult:
        papers = []
        for item in data.get("data", []):
            paper = self._parse_paper(item)
            if paper:
                papers.append(paper)
        return SearchResult(
            query=query,
            total_results=data.get("total", len(papers)),
            papers=papers,
            source="semantic_scholar",
        )

    def _parse_paper(self, item: dict) -> Optional[Paper]:
        if not item:
            return None
        try:
            authors = []
            for author in item.get("authors", []):
                name = author.get("name", "")
                if name:
                    authors.append(name)

            external_ids = item.get("externalIds", {}) or {}
            doi = external_ids.get("DOI")
            if doi and not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"

            oa_pdf = item.get("openAccessPdf") or {}
            pdf_url = oa_pdf.get("url")

            return Paper(
                title=item.get("title", "Untitled"),
                authors=authors,
                journal=item.get("venue"),
                doi=doi,
                year=item.get("year"),
                citation_count=item.get("citationCount", 0),
                abstract=item.get("abstract"),
                open_access=bool(pdf_url),
                pdf_url=pdf_url,
                source="semantic_scholar",
                references_count=len(item.get("references", [])),
            )
        except Exception:
            return None
