from pydantic import BaseModel, Field
from typing import Optional, List


class Paper(BaseModel):
    title: str
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    publisher: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = 0
    abstract: Optional[str] = None
    open_access: bool = False
    pdf_url: Optional[str] = None
    url: Optional[str] = None
    source: str = "unknown"
    references_count: int = 0
    influential_citation_count: int = 0

    def short_authors(self, max_authors: int = 3) -> str:
        if not self.authors:
            return "N/A"
        if len(self.authors) <= max_authors:
            return ", ".join(self.authors)
        return ", ".join(self.authors[:max_authors]) + " et al."

    def display_year(self) -> str:
        return str(self.year) if self.year else "N/A"

    def display_citations(self) -> str:
        return str(self.citation_count) if self.citation_count > 0 else "-"

    def display_oa(self) -> str:
        return "✓" if self.open_access else "✗"


class SearchResult(BaseModel):
    query: str
    total_results: int = 0
    papers: List[Paper] = Field(default_factory=list)
    source: str = "unknown"
