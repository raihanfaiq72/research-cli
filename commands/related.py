from typing import Optional
from utils.console import console, show_search_results, show_error, show_spinner
from services.openalex_service import OpenAlexService
from services.semantic_service import SemanticScholarService
from services.crossref_service import CrossrefService
from models.paper import Paper


def fetch_related(doi: str, limit: int = 10):
    services = [
        ("OpenAlex", OpenAlexService()),
        ("Semantic Scholar", SemanticScholarService()),
    ]

    all_papers = []

    for name, service in services:
        try:
            result = service.fetch_related(doi, limit=limit)
            for paper in result.papers:
                if paper.title and paper.title != "Untitled":
                    if not any(
                        p.doi and p.doi == paper.doi for p in all_papers if p.doi
                    ):
                        all_papers.append(paper)
        except Exception:
            continue

    if all_papers:
        show_search_results(all_papers[:limit], f"Related Papers for DOI: {doi}")
    else:
        show_error(f"No related papers found for DOI '{doi}'.")

    return all_papers[:limit]
