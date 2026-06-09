#!/usr/bin/env python3
import os
import sys
import typer
from typing import Optional
from utils.console import console, show_banner, show_error
from commands.search import search_papers
from commands.doi import fetch_by_doi
from commands.abstract import fetch_abstract
from commands.pdf import find_pdf, download_pdf
from commands.pdf_translate import pdf_translate
from commands.related import fetch_related
from commands.trend import show_trend
from commands.export import export_results
from commands.reading_list import add_to_reading_list, remove_from_reading_list, list_reading_list
from models.paper import Paper

app = typer.Typer(
    name="research",
    help="Academic Research Assistant CLI",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    epilog="""
  Examples:

    research search "microservices architecture"

    research search "digital agri" --year 2020-2026

    research doi 10.1016/j.njas.2019.100315

    research abstract 10.1016/j.njas.2019.100315

    research pdf 10.1016/j.njas.2019.100315

    research download 10.1016/j.njas.2019.100315 --output ./pdfs

    research related 10.1016/j.njas.2019.100315 --limit 15

    research pdf-translate https://example.com/paper.pdf --to eng

    research pdf-translate paper.pdf --to eng,idn

    research trend "microservices" --start 2020 --end 2024

    research search "software arch" --limit 5

    research save 1,2,3

    research reading-list

    research remove 1,2,3

    research export bibtex --output references.bib

    research export csv

    research export markdown --output papers.md
""",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        show_banner()
        console.print("\nUse [bold]research --help[/bold] for available commands.")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for academic papers"),
    year: Optional[str] = typer.Option(
        None, "--year", "-y", help="Year range filter, e.g. 2020-2026"
    ),
    limit: int = typer.Option(
        20, "--limit", "-l", help="Number of results to return"
    ),
    sort: str = typer.Option(
        "relevance",
        "--sort",
        "-s",
        help="Sort by: relevance, citations, year",
    ),
):
    """Search for academic papers by keyword.

    Examples:

      $ research search "microservices architecture"
      $ research search "digital agriculture" --year 2020-2026
      $ research search "software architecture" --sort citations --limit 10
    """
    if sort not in ("relevance", "citations", "year"):
        show_error("Sort must be one of: relevance, citations, year")
        raise typer.Exit(1)
    papers = search_papers(query, year=year, limit=limit, sort_by=sort)
    return papers


@app.command()
def doi(
    doi: str = typer.Argument(..., help="Digital Object Identifier (DOI)"),
):
    """Fetch paper details by DOI.

    Examples:

      $ research doi 10.1016/j.njas.2019.100315
    """
    fetch_by_doi(doi)


@app.command()
def abstract(
    doi: str = typer.Argument(..., help="Digital Object Identifier (DOI)"),
):
    """Fetch abstract of a paper by DOI.

    Examples:

      $ research abstract 10.1016/j.njas.2019.100315
    """
    fetch_abstract(doi)


@app.command()
def pdf(
    doi: str = typer.Argument(..., help="Digital Object Identifier (DOI)"),
):
    """Find open access PDF URL for a paper by DOI.

    Searches Unpaywall, CORE, OpenAlex, and arXiv for a freely
    available PDF. Some papers are behind paywalls and won't be found.

    Examples:

      $ research pdf 10.1016/j.njas.2019.100315
    """
    find_pdf(doi)


@app.command()
def download(
    doi: str = typer.Argument(..., help="Digital Object Identifier (DOI)"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory for downloaded PDF"
    ),
):
    """Download PDF for a paper by DOI.

    Finds a PDF URL from open access sources, verifies it points to
    an actual PDF file, and downloads it with a progress bar.

    Only works for Open Access papers. Paywalled papers
    (IEEE, Springer, Elsevier) cannot be downloaded.

    Examples:

      $ research download 10.1016/j.njas.2019.100315
      $ research download 10.1109/ms.2016.64 --output ./pdfs
    """
    download_pdf(doi, output_dir=output or None)


@app.command("pdf-translate")
def pdf_translate_cmd(
    source: str = typer.Argument(
        ..., help="PDF URL or local file path"
    ),
    to: str = typer.Option(
        "eng", "--to", "-t", help="Target language(s): eng, idn (comma-separated)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Custom output directory"
    ),
):
    """Translate a PDF to English and/or Indonesian.

    Extracts text from a PDF (URL or local file), detects the original
    language, and translates to the specified target language(s). Saves
    the original and translated PDFs in pdf_translate_process/.

    Examples:

      $ research pdf-translate https://example.com/paper.pdf --to eng

      $ research pdf-translate https://example.com/paper.pdf --to idn

      $ research pdf-translate paper.pdf --to eng,idn --output ./my_translations
    """
    langs = [l.strip() for l in to.split(",")]
    pdf_translate(source, langs, output_dir=output)


@app.command("translate")
def translate_cmd(
    source: str = typer.Argument(
        ..., help="PDF URL or local file path"
    ),
    to: str = typer.Option(
        "eng", "--to", "-t", help="Target language(s): eng, idn (comma-separated)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Custom output directory"
    ),
):
    """Shorthand for [bold]pdf-translate[/bold].

    Translates a PDF to English and/or Indonesian.
    Usage and options are identical to [bold]pdf-translate[/bold].

    Examples:

      $ research translate https://example.com/paper.pdf --to eng

      $ research translate paper.pdf --to eng,idn
    """
    langs = [l.strip() for l in to.split(",")]
    pdf_translate(source, langs, output_dir=output)


@app.command()
def related(
    doi: str = typer.Argument(..., help="Digital Object Identifier (DOI)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of related papers"),
):
    """Find related papers by DOI.

    Uses OpenAlex and Semantic Scholar to find papers related
    to the given DOI. Useful for literature review exploration.

    Examples:

      $ research related 10.1016/j.njas.2019.100315
      $ research related 10.1016/j.njas.2019.100315 --limit 15
    """
    fetch_related(doi, limit=limit)


@app.command()
def trend(
    query: str = typer.Argument(..., help="Research topic or keyword"),
    start: int = typer.Option(2019, "--start", "-s", help="Start year"),
    end: int = typer.Option(2026, "--end", "-e", help="End year"),
):
    """Show publication trend for a keyword.

    Displays a bar chart of publication counts per year
    using data from OpenAlex.

    Examples:

      $ research trend "microservices"
      $ research trend "digital agriculture" --start 2020 --end 2026
    """
    show_trend(query, start_year=start, end_year=end)


@app.command()
def save(
    indices: str = typer.Argument(
        ..., help="Paper indices to save, comma-separated (e.g. 1,2,3)"
    ),
):
    """Save search results to reading list by index.

    Run 'research search' first to populate results, then
    use the row numbers from the results table to save.

    Examples:

      $ research search "microservices" --limit 10
      $ research save 1,2,3
    """
    from commands.search import get_last_results

    papers = get_last_results()
    if not papers:
        show_error("No search results available. Run 'research search' first.")
        return

    try:
        indices_list = [int(i.strip()) for i in indices.split(",")]
    except ValueError:
        show_error("Indices must be comma-separated numbers.")
        return

    add_to_reading_list(papers, indices_list)


@app.command()
def reading_list():
    """Display your reading list.

    Shows all papers you've saved using the 'save' command.
    Papers are stored persistently in data/reading_list.json.

    Examples:

      $ research reading-list
    """
    list_reading_list()


@app.command()
def remove(
    indices: str = typer.Argument(
        ..., help="Paper indices to remove, comma-separated (e.g. 1,2,3)"
    ),
):
    """Remove papers from reading list by index.

    Use row numbers from 'research reading-list' output.
    Prompts for confirmation before removing.

    Examples:

      $ research remove 1
      $ research remove 1,2,3
    """
    try:
        indices_list = [int(i.strip()) for i in indices.split(",")]
    except ValueError:
        show_error("Indices must be comma-separated numbers.")
        return
    remove_from_reading_list(indices_list)


@app.command()
def export(
    fmt: str = typer.Argument(
        ..., help="Export format: csv, bibtex, markdown"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Export papers to CSV, BibTeX, or Markdown.

    Exports all papers from your reading list. If no --output
    is given, prints to stdout.

    Examples:

      $ research export csv
      $ research export csv --output papers.csv
      $ research export bibtex --output references.bib
      $ research export markdown --output papers.md
    """
    from commands.reading_list import get_reading_list_papers
    papers = get_reading_list_papers()
    export_results(papers, fmt, output)


if __name__ == "__main__":
    try:
        app()
    except SystemExit:
        # Detect if user passed a file path or URL as a command name
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            if (
                arg.endswith(".pdf")
                or os.path.exists(arg)
                or arg.startswith(("http://", "https://"))
            ):
                console.print(
                    f"\n[yellow]Tip: Did you mean [bold]research pdf-translate {arg}[/bold]?"
                )
                console.print(
                    "  Or use [bold]research translate[/bold] as shorthand.\n"
                )
        raise
