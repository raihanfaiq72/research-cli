import csv
import io
from typing import List
from models.paper import Paper


def export_csv(papers: List[Paper]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Title", "Authors", "Year", "Journal", "Publisher",
        "DOI", "Citations", "Open Access", "PDF URL", "Abstract"
    ])
    for paper in papers:
        writer.writerow([
            paper.title,
            "; ".join(paper.authors),
            paper.display_year(),
            paper.journal or "",
            paper.publisher or "",
            paper.doi or "",
            paper.display_citations(),
            "Yes" if paper.open_access else "No",
            paper.pdf_url or "",
            (paper.abstract or "").replace("\n", " "),
        ])
    return output.getvalue()


def export_bibtex(papers: List[Paper]) -> str:
    entries = []
    for i, paper in enumerate(papers):
        bibkey = _generate_bibkey(paper, i)
        authors = " and ".join(paper.authors) if paper.authors else "Unknown"
        entry_parts = [
            f"@article{{{bibkey},",
            f"  title = {{{paper.title}}}",
            f"  author = {{{authors}}}",
            f"  year = {{{paper.display_year()}}}",
        ]
        if paper.journal:
            entry_parts.append(f"  journal = {{{paper.journal}}}")
        if paper.publisher:
            entry_parts.append(f"  publisher = {{{paper.publisher}}}")
        if paper.doi:
            entry_parts.append(f"  doi = {{{paper.doi}}}")
        if paper.abstract:
            abstract_clean = paper.abstract.replace("\n", " ").replace("{", "\\{").replace("}", "\\}")
            entry_parts.append(f"  abstract = {{{abstract_clean}}}")
        entry_parts.append("}")
        entries.append("\n".join(entry_parts))
    return "\n\n".join(entries)


def export_markdown(papers: List[Paper]) -> str:
    lines = [
        "# Research Papers\n",
        f"| # | Year | Title | Authors | Citations | DOI |",
        "|---|------|-------|---------|-----------|-----|",
    ]
    for idx, paper in enumerate(papers, 1):
        authors_short = (
            ", ".join(paper.authors[:3]) + " et al."
            if len(paper.authors) > 3
            else ", ".join(paper.authors) if paper.authors else "N/A"
        )
        doi_str = paper.doi if paper.doi else "N/A"
        lines.append(
            f"| {idx} | {paper.display_year()} | {paper.title} | "
            f"{authors_short} | {paper.display_citations()} | {doi_str} |"
        )

    return "\n".join(lines)


def _generate_bibkey(paper: Paper, index: int) -> str:
    if paper.authors:
        last_name = paper.authors[0].split(",")[0].split()[-1].lower()
    else:
        last_name = "unknown"
    year = paper.year if paper.year else "0000"
    title_words = paper.title.split()[:3]
    title_part = "".join(w.lower() for w in title_words if w[0].isalpha())[:15]
    return f"{last_name}{year}{title_part}"
