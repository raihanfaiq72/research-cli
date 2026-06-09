from typing import List
from models.paper import Paper


def format_authors(authors: List[str], max_authors: int = 5) -> str:
    if not authors:
        return "N/A"
    if len(authors) <= max_authors:
        return ", ".join(authors)
    return ", ".join(authors[:max_authors]) + " et al."


def format_abstract(abstract: str, max_length: int = 300) -> str:
    if not abstract:
        return "No abstract available."
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(" ", 1)[0] + "..."


def truncate_text(text: str, max_length: int = 60) -> str:
    if not text or len(text) <= max_length:
        return text or "N/A"
    return text[: max_length - 3] + "..."


def format_citation_count(count: int) -> str:
    if count == 0:
        return "-"
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return str(count)
