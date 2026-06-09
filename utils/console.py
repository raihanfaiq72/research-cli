from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from pyfiglet import Figlet
from typing import Optional, List
from models.paper import Paper

console = Console()


def show_banner():
    figlet = Figlet(font="slant")
    banner_text = figlet.renderText("Research CLI")
    banner = Panel(
        banner_text,
        subtitle="Academic Research Assistant v1.0",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(banner)


def show_spinner(message: str):
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def show_search_results(papers: List[Paper], title: str = "Search Results"):
    if not papers:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(title=title, border_style="cyan", header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Year", width=6)
    table.add_column("Title", width=60)
    table.add_column("Citations", width=10, justify="right")
    table.add_column("OA", width=4, justify="center")

    for idx, paper in enumerate(papers, 1):
        table.add_row(
            str(idx),
            paper.display_year(),
            paper.title[:57] + "..." if len(paper.title) > 57 else paper.title,
            paper.display_citations(),
            paper.display_oa(),
        )

    console.print(table)


def show_paper_detail(paper: Paper):
    details = [
        f"[bold]Title:[/bold] {paper.title}",
        f"[bold]Authors:[/bold] {', '.join(paper.authors) if paper.authors else 'N/A'}",
        f"[bold]Year:[/bold] {paper.display_year()}",
        f"[bold]Journal:[/bold] {paper.journal or 'N/A'}",
        f"[bold]Publisher:[/bold] {paper.publisher or 'N/A'}",
        f"[bold]DOI:[/bold] {paper.doi or 'N/A'}",
        f"[bold]Citations:[/bold] {paper.display_citations()}",
        f"[bold]Open Access:[/bold] {'Yes' if paper.open_access else 'No'}",
        f"[bold]PDF URL:[/bold] {paper.pdf_url or 'N/A'}",
        f"[bold]Source:[/bold] {paper.source}",
    ]

    if paper.abstract:
        details.append(f"\n[bold]Abstract:[/bold]\n{paper.abstract}")

    panel = Panel(
        "\n".join(details),
        title="Paper Details",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)


def show_trend_chart(yearly_counts: dict, title: str = "Research Trend"):
    if not yearly_counts:
        console.print("[yellow]No trend data available.[/yellow]")
        return

    max_count = max(yearly_counts.values()) if yearly_counts else 1
    sorted_years = sorted(yearly_counts.keys())

    lines = [f"[bold]{title}[/bold]\n"]
    for year in sorted_years:
        count = yearly_counts[year]
        bar_length = int((count / max_count) * 30) if max_count > 0 else 0
        bar = "█" * bar_length
        lines.append(f"  {year} {bar} {count}")

    panel = Panel("\n".join(lines), border_style="blue", padding=(1, 2))
    console.print(panel)


def show_message(message: str, style: str = "green"):
    console.print(f"[{style}]{message}[/{style}]")


def show_error(message: str):
    console.print(f"[bold red]Error:[/bold red] {message}")


def confirm_action(message: str) -> bool:
    result = console.input(f"[yellow]{message} (y/n): [/yellow]")
    return result.strip().lower() == "y"
