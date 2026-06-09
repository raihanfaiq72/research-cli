from typing import Optional
import requests
import xml.etree.ElementTree as ET
from config import settings
from models.paper import Paper, SearchResult
from utils.cache import get_cache, set_cache


class ArxivService:
    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        self.timeout = settings.request_timeout

    def search(self, query: str, year_range: Optional[str] = None,
               limit: int = 20, page: int = 1) -> SearchResult:
        cache_key = f"search_{query}_{year_range}_{limit}_{page}"
        cached = get_cache("arxiv", cache_key)
        if cached:
            return SearchResult(**cached)

        start = (page - 1) * limit
        search_query = f"all:{query}"
        if year_range:
            years = year_range.split("-")
            search_query = (
                f"all:{query} AND submittedDate:[{years[0]}0101 TO {years[1]}1231]"
            )

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(limit, 300),
        }

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            response.raise_for_status()
            result = self._parse_response(response.text, query)
            set_cache("arxiv", cache_key, result.model_dump())
            return result
        except requests.RequestException:
            return SearchResult(query=query, source="arxiv", total_results=0)

    def fetch_by_doi(self, doi: str) -> Optional[Paper]:
        cache_key = f"doi_{doi}"
        cached = get_cache("arxiv", cache_key)
        if cached:
            return Paper(**cached)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        search_query = f"doi:{doi_clean}"
        params = {"search_query": search_query, "max_results": 3}

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            response.raise_for_status()
            result = self._parse_response(response.text, doi)
            if result.papers:
                paper = result.papers[0]
                set_cache("arxiv", cache_key, paper.model_dump())
                return paper
            return None
        except requests.RequestException:
            return None

    def fetch_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        params = {"id_list": arxiv_id, "max_results": 1}
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "ResearchCLI/1.0"},
            )
            response.raise_for_status()
            result = self._parse_response(response.text, arxiv_id)
            return result.papers[0] if result.papers else None
        except requests.RequestException:
            return None

    def _parse_response(self, xml_text: str, query: str) -> SearchResult:
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        }
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return SearchResult(query=query, source="arxiv", total_results=0)

        total_results_el = root.find(".//opensearch:totalResults", ns)
        total_results = int(total_results_el.text) if total_results_el is not None else 0

        papers = []
        for entry in root.findall("atom:entry", ns):
            paper = self._parse_entry(entry, ns)
            if paper:
                papers.append(paper)

        return SearchResult(
            query=query,
            total_results=total_results,
            papers=papers,
            source="arxiv",
        )

    def _parse_entry(self, entry, ns) -> Optional[Paper]:
        try:
            title = entry.find("atom:title", ns)
            title_text = title.text.strip().replace("\n", " ") if title is not None else "Untitled"

            summary = entry.find("atom:summary", ns)
            abstract = summary.text.strip().replace("\n", " ") if summary is not None else None

            authors = []
            for author_el in entry.findall("atom:author", ns):
                name_el = author_el.find("atom:name", ns)
                if name_el is not None:
                    authors.append(name_el.text.strip())

            published = entry.find("atom:published", ns)
            year = int(published.text[:4]) if published is not None else None

            links = entry.findall("atom:link", ns)
            pdf_url = None
            for link in links:
                if link.get("title") == "pdf":
                    pdf_url = link.get("href")
                    break

            doi = None
            arxiv_doi = entry.find("arxiv:doi", ns)
            if arxiv_doi is not None:
                doi_val = arxiv_doi.text.strip()
                doi = f"https://doi.org/{doi_val}" if doi_val else None

            arxiv_id_el = entry.find("atom:id", ns)
            arxiv_url = arxiv_id_el.text.strip() if arxiv_id_el is not None else None

            return Paper(
                title=title_text,
                authors=authors,
                doi=doi,
                year=year,
                abstract=abstract,
                open_access=True,
                pdf_url=pdf_url,
                url=arxiv_url,
                source="arxiv",
            )
        except Exception:
            return None
