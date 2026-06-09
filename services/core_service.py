from typing import Optional
import requests
from config import settings
from models.paper import Paper, SearchResult
from utils.cache import get_cache, set_cache


class CoreService:
    BASE_URL = "https://api.core.ac.uk/v3"

    def __init__(self):
        self.api_key = settings.core_api_key
        self.timeout = settings.request_timeout

    def _headers(self) -> dict:
        headers = {"User-Agent": "ResearchCLI/1.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def search(self, query: str, year_range: Optional[str] = None,
               limit: int = 20, page: int = 1) -> SearchResult:
        if not self.api_key:
            return SearchResult(query=query, source="core", total_results=0)

        cache_key = f"search_{query}_{year_range}_{limit}_{page}"
        cached = get_cache("core", cache_key)
        if cached:
            return SearchResult(**cached)

        params = {
            "q": query,
            "limit": min(limit, 100),
            "offset": (page - 1) * limit,
        }
        if year_range:
            params["yearRange"] = year_range

        try:
            response = requests.get(
                f"{self.BASE_URL}/search/outputs",
                params=params,
                timeout=self.timeout,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
            result = self._parse_search_response(data, query)
            set_cache("core", cache_key, result.model_dump())
            return result
        except requests.RequestException:
            return SearchResult(query=query, source="core", total_results=0)

    def find_pdf(self, doi: str) -> Optional[Paper]:
        if not self.api_key:
            return None

        cache_key = f"pdf_{doi}"
        cached = get_cache("core", cache_key)
        if cached:
            return Paper(**cached)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        try:
            response = requests.get(
                f"{self.BASE_URL}/outputs/doi:{doi_clean}",
                timeout=self.timeout,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
            paper = self._parse_paper(data)
            if paper:
                set_cache("core", cache_key, paper.model_dump())
            return paper
        except requests.RequestException:
            return None

    def _parse_search_response(self, data: dict, query: str) -> SearchResult:
        results = data.get("results", [])
        papers = []
        for item in results:
            paper = self._parse_paper(item)
            if paper:
                papers.append(paper)
        return SearchResult(
            query=query,
            total_results=data.get("totalResults", len(papers)),
            papers=papers,
            source="core",
        )

    def _parse_paper(self, item: dict) -> Optional[Paper]:
        try:
            authors = []
            for author in item.get("authors", []):
                name = author.get("name", "")
                if name:
                    authors.append(name)

            doi = item.get("doi")
            if doi and not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"

            full_text_url = item.get("fullTextUrl")
            pdf_url = (
                full_text_url
                if full_text_url
                else item.get("downloadUrl")
            )

            return Paper(
                title=item.get("title", "Untitled"),
                authors=authors,
                doi=doi,
                year=item.get("yearPublished"),
                citation_count=item.get("citationCount", 0),
                abstract=item.get("abstract"),
                open_access=item.get("openAccess", False),
                pdf_url=pdf_url,
                source="core",
                journal=item.get("journal", {}).get("name") if item.get("journal") else None,
                publisher=item.get("publisher"),
            )
        except Exception:
            return None
