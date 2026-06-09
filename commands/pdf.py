import os
import re
import httpx
from rich.progress import (
    Progress, BarColumn, DownloadColumn, TransferSpeedColumn,
    TextColumn, TimeRemainingColumn,
)
from utils.console import console, show_paper_detail, show_error, show_message
from services.unpaywall_service import UnpaywallService
from services.core_service import CoreService
from services.openalex_service import OpenAlexService
from services.arxiv_service import ArxivService

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")


def _sanitize_filename(title: str, doi: str) -> str:
    name = title if title else doi
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    return name[:100] + ".pdf"


def _is_pdf_url(url: str) -> bool:
    path = url.split("?")[0]
    return path.endswith(".pdf") or "/pdf/" in path


def _resolve_pdf_url(client: httpx.Client, url: str) -> str | None:
    """Follow redirects and return resolved URL."""
    try:
        resp = client.head(url, follow_redirects=True, timeout=30)
        resolved = str(resp.url)
        ct = resp.headers.get("content-type", "")
        if "application/pdf" in ct:
            return resolved
        if _is_pdf_url(resolved):
            return resolved
        return None
    except httpx.RequestError:
        return None


def _try_find_arxiv_pdf(doi: str) -> str | None:
    """Search arXiv for a PDF by DOI."""
    import requests
    import xml.etree.ElementTree as ET
    doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    try:
        r = requests.get(
            f"http://export.arxiv.org/api/query?search_query=doi:{doi_clean}&max_results=3",
            timeout=15,
        )
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    return link.get("href")
    except Exception:
        return None
    return None


def download_pdf(doi: str, output_dir: str | None = None):
    if output_dir is None:
        output_dir = DOWNLOAD_DIR

    # First, try to find actual PDF URLs
    pdf_urls = []

    # Check arXiv directly (best PDF source)
    arxiv_pdf = _try_find_arxiv_pdf(doi)
    if arxiv_pdf:
        pdf_urls.append(("arXiv", arxiv_pdf))

    # Use the existing find_pdf machinery
    found = find_pdf(doi, interactive=False)
    if found:
        for name, url, paper in found:
            if url and url not in [u for _, u in pdf_urls]:
                pdf_urls.append((name, url))

    if not pdf_urls:
        show_error(f"No PDF source found for DOI '{doi}'. This paper may be behind a paywall.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    paper = found[0][2] if found else None
    filename = _sanitize_filename(paper.title if paper else "", doi)
    filepath = os.path.join(output_dir, filename)

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for source_name, pdf_url in pdf_urls:
            # Resolve URL to check if it's actually a PDF
            resolved = _resolve_pdf_url(client, pdf_url)
            if not resolved:
                show_message(
                    f"[{source_name}] URL doesn't point to a PDF (redirects to non-PDF): {pdf_url}",
                    "yellow",
                )
                continue

            show_message(f"Downloading from [{source_name}]: {resolved}", "cyan")

            try:
                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    console=console,
                ) as progress:
                    with client.stream("GET", resolved) as response:
                        if response.status_code != 200:
                            show_message(
                                f"[{source_name}] HTTP {response.status_code}, trying next...",
                                "yellow",
                            )
                            continue

                        total = int(response.headers.get("content-length", 0))
                        task = progress.add_task(
                            f"Downloading {filename}", total=total
                        )

                        with open(filepath, "wb") as f:
                            for chunk in response.iter_bytes(chunk_size=65536):
                                f.write(chunk)
                                progress.update(task, advance=len(chunk))

                file_size = os.path.getsize(filepath)
                show_message(
                    f"PDF saved: {filepath} ({file_size / 1024:.1f} KB)",
                    "green",
                )
                return filepath

            except (httpx.RequestError, OSError) as e:
                show_message(
                    f"[{source_name}] Download failed: {e}, trying next...",
                    "yellow",
                )
                continue

    show_error(f"Could not download PDF for DOI '{doi}'. The paper may be behind a paywall.")
    show_message(
        "Try checking if a free preprint is available on arXiv, the author's website, "
        "or an institutional repository.",
        "yellow",
    )
    return None


def find_pdf(doi: str, interactive: bool = True):
    services = [
        ("Unpaywall", UnpaywallService()),
        ("CORE", CoreService()),
        ("OpenAlex", OpenAlexService()),
        ("arXiv", ArxivService()),
    ]

    found_sources = []

    for name, service in services:
        try:
            if name == "OpenAlex":
                paper = service.fetch_by_doi(doi)
            else:
                paper = service.find_pdf(doi) if hasattr(service, "find_pdf") else service.fetch_by_doi(doi)

            if paper and paper.pdf_url:
                found_sources.append((name, paper.pdf_url, paper))
        except Exception:
            continue

    if interactive:
        if found_sources:
            console.print("[bold green]PDF Sources Found:[/bold green]\n")
            for name, url, paper in found_sources:
                console.print(f"  [{name}] {url}")
            console.print()

            best = found_sources[0]
            paper = best[2]
            if paper:
                show_paper_detail(paper)
        else:
            show_error(f"No open access PDF found for DOI '{doi}'.")
            show_message(
                "Try checking the paper's repository or contact the authors.",
                "yellow",
            )

    return found_sources
