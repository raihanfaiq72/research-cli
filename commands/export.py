from typing import Optional, List
from utils.console import console, show_message, show_error
from utils.exporter import export_csv, export_bibtex, export_markdown
from commands.reading_list import get_reading_list_papers
from models.paper import Paper


def export_results(papers: List[Paper], fmt: str, output_path: Optional[str] = None):
    if not papers:
        papers = get_reading_list_papers()
    if not papers:
        show_error("No papers to export. Please search first or add to reading list.")
        return

    if fmt == "csv":
        content = export_csv(papers)
        ext = "csv"
    elif fmt == "bibtex":
        content = export_bibtex(papers)
        ext = "bib"
    elif fmt == "markdown":
        content = export_markdown(papers)
        ext = "md"
    else:
        show_error(f"Unsupported format: {fmt}")
        return

    if output_path:
        try:
            with open(output_path, "w") as f:
                f.write(content)
            show_message(f"Exported {len(papers)} papers to {output_path}", "green")
        except OSError as e:
            show_error(f"Failed to write file: {e}")
    else:
        console.print(content)
        show_message(f"\nExported {len(papers)} papers in {fmt} format.", "green")
