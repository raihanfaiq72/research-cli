from utils.console import console, show_paper_detail, show_error
from services.openalex_service import OpenAlexService
from services.europepmc_service import EuropePMCService
from services.semantic_service import SemanticScholarService


def fetch_abstract(doi: str):
    services = [
        ("OpenAlex", OpenAlexService()),
        ("Europe PMC", EuropePMCService()),
        ("Semantic Scholar", SemanticScholarService()),
    ]

    for name, service in services:
        try:
            paper = service.fetch_by_doi(doi)
            if paper and paper.abstract:
                console.print(
                    f"[bold cyan]Abstract from {name}[/bold cyan]\n"
                )
                console.print(paper.abstract)
                return paper
        except Exception:
            continue

    show_error(f"Abstract not found for DOI '{doi}'.")
    return None
