import json
import os
from typing import Optional, List
from rich.progress import Progress, SpinnerColumn, TextColumn
from utils.console import console, show_search_results, show_error, show_message
from services.openalex_service import OpenAlexService
from services.crossref_service import CrossrefService
from services.semantic_service import SemanticScholarService
from services.core_service import CoreService
from services.arxiv_service import ArxivService
from services.europepmc_service import EuropePMCService
from models.paper import Paper

LAST_SEARCH_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "last_search.json"
)


def _save_last_results(papers: List[Paper]):
    os.makedirs(os.path.dirname(LAST_SEARCH_FILE), exist_ok=True)
    with open(LAST_SEARCH_FILE, "w") as f:
        json.dump([p.model_dump() for p in papers], f, indent=2)


def get_last_results() -> List[Paper]:
    if not os.path.exists(LAST_SEARCH_FILE):
        return []
    try:
        with open(LAST_SEARCH_FILE, "r") as f:
            data = json.load(f)
        return [Paper(**item) for item in data]
    except (json.JSONDecodeError, OSError):
        return []


def search_papers(
    query: str,
    year: Optional[str] = None,
    limit: int = 200,
    sort_by: str = "relevance",
    page: int = 1,
):
    services = {
        "OpenAlex": OpenAlexService(),
        "Semantic Scholar": SemanticScholarService(),
        "Crossref": CrossrefService(),
    }

    all_papers = []
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )

    with progress:
        tasks = []
        for name, service in services.items():
            task = progress.add_task(f"Searching {name}...", total=None)
            tasks.append((name, service, task))

        for name, service, task in tasks:
            try:
                result = service.search(query, year_range=year, limit=limit)
                for paper in result.papers:
                    if paper.title and paper.title != "Untitled":
                        if not any(
                            p.doi and p.doi == paper.doi for p in all_papers if p.doi
                        ):
                            all_papers.append(paper)
                progress.remove_task(task)
            except Exception:
                progress.remove_task(task)
                continue

    all_papers = _deduplicate(all_papers)

    if sort_by == "citations":
        all_papers.sort(key=lambda p: p.citation_count, reverse=True)
    elif sort_by == "year":
        all_papers.sort(key=lambda p: p.year or 0, reverse=True)

    _save_last_results(all_papers)

    total = len(all_papers)
    start = (page - 1) * limit
    end = start + limit
    page_papers = all_papers[start:end]

    total_pages = max(1, (total + limit - 1) // limit)

    title = f'Search Results for "{query}"'
    if total_pages > 1:
        title += f" (Page {page}/{total_pages})"

    show_search_results(page_papers, title)
    show_message(
        f"Found {total} unique papers across multiple sources. "
        + (f"Showing page {page}/{total_pages}." if total_pages > 1 else ""),
        "blue",
    )

    return all_papers


def _deduplicate(papers: list) -> list:
    seen_dois = set()
    seen_titles = set()
    unique = []
    for paper in papers:
        if paper.doi and paper.doi in seen_dois:
            continue
        title_lower = paper.title.lower().strip() if paper.title else ""
        if title_lower and title_lower in seen_titles:
            continue
        if paper.doi:
            seen_dois.add(paper.doi)
        if title_lower:
            seen_titles.add(title_lower)
        unique.append(paper)
    return unique
