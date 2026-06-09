from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn
from utils.console import console, show_trend_chart, show_error
from services.openalex_service import OpenAlexService


def show_trend(query: str, start_year: int = 2019, end_year: int = 2026):
    service = OpenAlexService()
    years = range(start_year, end_year + 1)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )

    yearly_counts = {}
    with progress:
        task = progress.add_task(
            f"Fetching trend data for '{query}'...", total=len(years)
        )
        try:
            yearly_counts = service.get_trend(query, years)
        except Exception:
            show_error("Failed to fetch trend data.")
            return
        finally:
            progress.remove_task(task)

    if yearly_counts:
        show_trend_chart(yearly_counts, f'Research Trend: "{query}"')
    else:
        show_error("No trend data available.")

    return yearly_counts
