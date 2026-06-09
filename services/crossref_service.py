from typing import Optional, List
import requests
from config import settings
from models.paper import Paper, SearchResult
from utils.cache import get_cache, set_cache


class CrossrefService:
    BASE_URL = "https://api.crossref.org"

    def __init__(self):
        self.timeout = settings.request_timeout
        self.max_retries = settings.max_retries
        self.mailto = settings.unpaywall_email or "research@example.com"

    def search(self, query: str, year_range: Optional[str] = None,
               limit: int = 20, page: int = 1) -> SearchResult:
        cache_key = f"search_{query}_{year_range}_{limit}_{page}"
        cached = get_cache("crossref", cache_key)
        if cached:
            return SearchResult(**cached)

        params = {
            "query": query,
            "rows": min(limit, 200),
            "offset": (page - 1) * limit,
            "mailto": self.mailto,
        }
        if year_range:
            years = year_range.split("-")
            params["filter"] = f"from-pub-date:{years[0]}-01-01,until-pub-date:{years[1]}-12-31"

        try:
            response = requests.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": f"ResearchCLI/1.0 (mailto:{self.mailto})"},
            )
            response.raise_for_status()
            data = response.json()
            result = self._parse_search_response(data, query)
            set_cache("crossref", cache_key, result.model_dump())
            return result
        except requests.RequestException:
            return SearchResult(query=query, source="crossref", total_results=0)

    def fetch_by_doi(self, doi: str) -> Optional[Paper]:
        cache_key = f"doi_{doi}"
        cached = get_cache("crossref", cache_key)
        if cached:
            return Paper(**cached)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        try:
            response = requests.get(
                f"{self.BASE_URL}/works/{doi_clean}",
                params={"mailto": self.mailto},
                timeout=self.timeout,
                headers={"User-Agent": f"ResearchCLI/1.0 (mailto:{self.mailto})"},
            )
            response.raise_for_status()
            data = response.json().get("message", {})
            paper = self._parse_work(data)
            if paper:
                set_cache("crossref", cache_key, paper.model_dump())
            return paper
        except requests.RequestException:
            return None

    def fetch_references(self, doi: str) -> List[Paper]:
        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        try:
            response = requests.get(
                f"{self.BASE_URL}/works/{doi_clean}",
                params={"mailto": self.mailto},
                timeout=self.timeout,
                headers={"User-Agent": f"ResearchCLI/1.0 (mailto:{self.mailto})"},
            )
            response.raise_for_status()
            data = response.json().get("message", {})
            refs = []
            for ref in data.get("reference", [])[:20]:
                ref_doi = ref.get("DOI")
                ref_paper = Paper(
                    title=ref.get("article-title", "Untitled"),
                    authors=[ref.get("author", "Unknown")],
                    journal=ref.get("journal-title"),
                    doi=f"https://doi.org/{ref_doi}" if ref_doi else None,
                    year=ref.get("year"),
                    source="crossref",
                )
                refs.append(ref_paper)
            return refs
        except requests.RequestException:
            return []

    def _parse_search_response(self, data: dict, query: str) -> SearchResult:
        message = data.get("message", {})
        items = message.get("items", [])
        papers = []
        for item in items:
            paper = self._parse_work(item)
            if paper:
                papers.append(paper)
        return SearchResult(
            query=query,
            total_results=message.get("total-results", len(papers)),
            papers=papers,
            source="crossref",
        )

    def _parse_work(self, work: dict) -> Optional[Paper]:
        try:
            authors = []
            for author in work.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)

            doi = work.get("DOI")
            if doi and not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"

            return Paper(
                title=work.get("title", ["Untitled"])[0],
                authors=authors,
                journal=work.get("container-title", [None])[0] if work.get("container-title") else None,
                publisher=work.get("publisher"),
                doi=doi,
                year=work.get("published-print", {}).get("date-parts", [[None]])[0][0]
                      or work.get("issued", {}).get("date-parts", [[None]])[0][0],
                citation_count=work.get("is-referenced-by-count", 0),
                abstract=work.get("abstract"),
                open_access=False,
                source="crossref",
            )
        except Exception:
            return None
