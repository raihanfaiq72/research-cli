from typing import Optional, List
import requests
from config import settings
from models.paper import Paper, SearchResult
from utils.cache import get_cache, set_cache


class OpenAlexService:
    BASE_URL = "https://api.openalex.org"

    def __init__(self):
        self.timeout = settings.request_timeout
        self.max_retries = settings.max_retries

    def search(self, query: str, year_range: Optional[str] = None,
               limit: int = 20, page: int = 1) -> SearchResult:
        cache_key = f"search_{query}_{year_range}_{limit}_{page}"
        cached = get_cache("openalex", cache_key)
        if cached:
            return SearchResult(**cached)

        params = {
            "search": query,
            "per-page": min(limit, 200),
            "page": page,
            "sort": "relevance_score:desc",
        }
        if year_range:
            params["filter"] = f"from_publication_date:{year_range.split('-')[0]}-01-01,to_publication_date:{year_range.split('-')[1]}-12-31"

        try:
            response = requests.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            result = self._parse_search_response(data, query)
            set_cache("openalex", cache_key, result.model_dump())
            return result
        except requests.RequestException as e:
            return SearchResult(query=query, source="openalex", total_results=0)

    def fetch_by_doi(self, doi: str) -> Optional[Paper]:
        cache_key = f"doi_{doi}"
        cached = get_cache("openalex", cache_key)
        if cached:
            return Paper(**cached)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        try:
            response = requests.get(
                f"{self.BASE_URL}/works/doi:{doi_clean}",
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            paper = self._parse_work(data)
            set_cache("openalex", cache_key, paper.model_dump())
            return paper
        except requests.RequestException:
            return None

    def fetch_related(self, doi: str, limit: int = 10) -> SearchResult:
        paper = self.fetch_by_doi(doi)
        if not paper:
            return SearchResult(query=doi, source="openalex", total_results=0)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        url = f"{self.BASE_URL}/works/doi:{doi_clean}"
        try:
            resp = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
            concept_id = None
            if data.get("concepts"):
                top_concept = max(data["concepts"], key=lambda c: c.get("score", 0))
                concept_id = top_concept.get("id")

            if concept_id:
                params = {
                    "filter": f"concept.id:{concept_id}",
                    "per-page": limit,
                    "sort": "cited_by_count:desc",
                }
                resp2 = requests.get(
                    f"{self.BASE_URL}/works",
                    params=params,
                    timeout=self.timeout,
                    headers={"User-Agent": "ResearchCLI/1.0"},
                )
                resp2.raise_for_status()
                related_data = resp2.json()
                return self._parse_search_response(related_data, f"related_to_{doi}")
        except requests.RequestException:
            pass

        return SearchResult(query=doi, source="openalex", total_results=0)

    def get_trend(self, query: str, years: range) -> dict:
        yearly_counts = {}
        for year in years:
            try:
                params = {
                    "search": query,
                    "filter": f"publication_year:{year}",
                    "per-page": 1,
                }
                response = requests.get(
                    f"{self.BASE_URL}/works",
                    params=params,
                    timeout=self.timeout,
                    headers={"User-Agent": "ResearchCLI/1.0"},
                )
                response.raise_for_status()
                data = response.json()
                yearly_counts[year] = data.get("meta", {}).get("count", 0)
            except requests.RequestException:
                yearly_counts[year] = 0
        return yearly_counts

    def _parse_search_response(self, data: dict, query: str) -> SearchResult:
        papers = []
        for work in data.get("results", []):
            paper = self._parse_work(work)
            if paper:
                papers.append(paper)
        return SearchResult(
            query=query,
            total_results=data.get("meta", {}).get("count", len(papers)),
            papers=papers,
            source="openalex",
        )

    def _parse_work(self, work: dict) -> Optional[Paper]:
        try:
            authors = []
            for authorship in work.get("authorships", []):
                author_name = authorship.get("author", {}).get("display_name", "")
                if author_name:
                    authors.append(author_name)

            oa_status = work.get("open_access", {})
            pdf_url = None
            if oa_status.get("is_oa"):
                pdf_url = oa_status.get("oa_url") or oa_status.get("pdf_url")

            return Paper(
                title=work.get("title", "Untitled"),
                authors=authors,
                journal=(
                    work.get("primary_location", {})
                    .get("source", {})
                    .get("display_name")
                ),
                publisher=(
                    work.get("primary_location", {})
                    .get("source", {})
                    .get("host_organization_name")
                ),
                doi=work.get("doi"),
                year=work.get("publication_year"),
                citation_count=work.get("cited_by_count", 0),
                abstract=work.get("abstract_inverted_index") and self._decode_abstract(
                    work["abstract_inverted_index"]
                ),
                open_access=oa_status.get("is_oa", False),
                pdf_url=pdf_url,
                url=work.get("id"),
                source="openalex",
                references_count=len(work.get("referenced_works", [])),
            )
        except Exception:
            return None

    def _decode_abstract(self, inverted_index: dict) -> Optional[str]:
        if not inverted_index:
            return None
        try:
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            return " ".join(w for _, w in word_positions)
        except Exception:
            return None
