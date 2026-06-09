from utils.console import console, show_paper_detail, show_error, show_spinner, show_message
from services.openalex_service import OpenAlexService
from services.crossref_service import CrossrefService
from services.semantic_service import SemanticScholarService
from services.europepmc_service import EuropePMCService
from models.paper import Paper


def fetch_by_doi(doi: str):
    services = [
        ("OpenAlex", OpenAlexService()),
        ("Semantic Scholar", SemanticScholarService()),
        ("Crossref", CrossrefService()),
        ("Europe PMC", EuropePMCService()),
    ]

    paper = None
    source_used = None

    for name, service in services:
        try:
            result = service.fetch_by_doi(doi)
            if result and result.title and result.title != "Untitled":
                paper = result
                source_used = name
                break
        except Exception:
            continue

    if paper:
        # Enrich with PDF info from other services
        pdf_sources = []
        for name, service in services:
            if name == source_used:
                continue
            try:
                result = service.fetch_by_doi(doi)
                if result and result.pdf_url and not paper.pdf_url:
                    paper.pdf_url = result.pdf_url
                    paper.open_access = True
                    pdf_sources.append(name)
            except Exception:
                continue

        show_paper_detail(paper)
        show_message(f"Source: {source_used}", "blue")
        if pdf_sources:
            show_message(f"PDF enriched by: {', '.join(pdf_sources)}", "green")
    else:
        show_error(f"Paper with DOI '{doi}' not found in any source.")

    return paper
