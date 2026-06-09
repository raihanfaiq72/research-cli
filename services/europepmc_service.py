from typing import Optional
import requests
from config import settings
from models.paper import Paper, SearchResult
from utils.cache import get_cache, set_cache


class EuropePMCService:
    BASE_URL = "https://www.ebi.ac.uk/europepmc/api"

    def __init__(self):
        self.timeout = settings.request_timeout

    def search(self, query: str, year_range: Optional[str] = None,
               limit: int = 20, page: int = 1) -> SearchResult:
        cache_key = f"search_{query}_{year_range}_{limit}_{page}"
        cached = get_cache("europepmc", cache_key)
        if cached:
            return SearchResult(**cached)

        params = {
            "query": query,
            "pageSize": min(limit, 100),
            "page": page,
            "format": "json",
            "sort": "CITED desc",
        }
        if year_range:
            params["query"] = f"({query}) AND (FIRST_PDATE:[{year_range.split('-')[0]}-01-01 TO {year_range.split('-')[1]}-12-31])"

        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            result = self._parse_search_response(data, query)
            set_cache("europepmc", cache_key, result.model_dump())
            return result
        except requests.RequestException:
            return SearchResult(query=query, source="europepmc", total_results=0)

    def fetch_by_doi(self, doi: str) -> Optional[Paper]:
        cache_key = f"doi_{doi}"
        cached = get_cache("europepmc", cache_key)
        if cached:
            return Paper(**cached)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        params = {"query": f"DOI:{doi_clean}", "format": "json"}

        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            result_list = data.get("resultList", {}).get("result", [])
            if result_list:
                paper = self._parse_paper(result_list[0])
                if paper:
                    set_cache("europepmc", cache_key, paper.model_dump())
                return paper
            return None
        except requests.RequestException:
            return None

    def _parse_search_response(self, data: dict, query: str) -> SearchResult:
        result_list = data.get("resultList", {}).get("result", [])
        papers = []
        for item in result_list:
            paper = self._parse_paper(item)
            if paper:
                papers.append(paper)
        return SearchResult(
            query=query,
            total_results=data.get("hitCount", len(papers)),
            papers=papers,
            source="europepmc",
        )

    def _parse_paper(self, item: dict) -> Optional[Paper]:
        try:
            authors = []
            author_str = item.get("authorString", "")
            if author_str:
                authors = [a.strip() for a in author_str.split(";") if a.strip()]

            doi = item.get("doi")
            if doi and not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"

            has_pdf = item.get("hasPDF", "N") == "Y"
            pdf_url = None
            if has_pdf:
                pdf_url = (
                    f"https://europepmc.org/articles/PMC{item.get('pmcid')}/pdf"
                    if item.get("pmcid")
                    else None
                )

            return Paper(
                title=item.get("title", "Untitled"),
                authors=authors,
                journal=item.get("journalTitle"),
                doi=doi,
                year=item.get("firstPublicationDate", "")[:4] if item.get("firstPublicationDate") else None,
                citation_count=item.get("citedByCount", 0),
                abstract=item.get("abstractText"),
                open_access=has_pdf or item.get("openAccess", "N") == "Y",
                pdf_url=pdf_url,
                source="europepmc",
            )
        except Exception:
            return None
