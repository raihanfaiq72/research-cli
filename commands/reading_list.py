import json
import os
from typing import List, Optional
from models.paper import Paper
from utils.console import (
    console,
    show_search_results,
    show_paper_detail,
    show_message,
    show_error,
    confirm_action,
)
from config import settings


def parse_indices(indices: str) -> List[int]:
    result = []
    for part in indices.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            parts = part.split("-")
            if len(parts) != 2:
                raise ValueError(f"Invalid range: {part}")
            start, end = int(parts[0].strip()), int(parts[1].strip())
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return result


def _load_reading_list() -> List[dict]:
    path = settings.reading_list_path
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_reading_list(items: List[dict]):
    path = settings.reading_list_path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(items, f, indent=2)


def add_to_reading_list(papers: List[Paper], indices: List[int]):
    items = _load_reading_list()
    existing_dois = {item.get("doi") for item in items if item.get("doi")}
    added = 0

    for idx in indices:
        if idx < 1 or idx > len(papers):
            show_error(f"Invalid index: {idx}")
            continue
        paper = papers[idx - 1]
        doi = paper.doi
        if doi and doi in existing_dois:
            show_message(f"Already in reading list: {paper.title[:50]}...", "yellow")
            continue

        item = paper.model_dump()
        items.append(item)
        if doi:
            existing_dois.add(doi)
        added += 1

    _save_reading_list(items)
    show_message(f"Added {added} paper(s) to reading list.", "green")


def remove_from_reading_list(indices: List[int]):
    items = _load_reading_list()
    if not items:
        show_error("Reading list is empty.")
        return

    if not confirm_action(
        f"Remove {len(indices)} paper(s) from reading list?"
    ):
        return

    indices_set = set(indices)
    new_items = [item for i, item in enumerate(items) if (i + 1) not in indices_set]
    removed = len(items) - len(new_items)
    _save_reading_list(new_items)
    show_message(f"Removed {removed} paper(s) from reading list.", "green")


def list_reading_list(search: str = "", year: Optional[str] = None, page: int = 1, limit: int = 200):
    items = _load_reading_list()
    if not items:
        show_message("Reading list is empty.", "yellow")
        return []

    papers = [Paper(**item) for item in items]

    if search:
        q = search.lower()
        papers = [p for p in papers if p.title and q in p.title.lower()]

    if year:
        if "-" in year:
            parts = year.split("-")
            try:
                y_start, y_end = int(parts[0]), int(parts[1])
                papers = [p for p in papers if p.year and y_start <= p.year <= y_end]
            except ValueError:
                show_error(f"Invalid year range: {year}")
                return []
        else:
            try:
                y = int(year)
                papers = [p for p in papers if p.year == y]
            except ValueError:
                show_error(f"Invalid year: {year}")
                return []

    total = len(papers)
    total_pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    page_papers = papers[start:start + limit]

    title = "Reading List"
    parts = []
    if search:
        parts.append(f'filter: "{search}"')
    if year:
        parts.append(f"year: {year}")
    if total_pages > 1:
        parts.append(f"Page {page}/{total_pages}")
    if parts:
        title += " (" + ", ".join(parts) + ")"

    show_search_results(page_papers, title)
    msg = f"Found {total} papers in reading list."
    if total_pages > 1:
        msg += f" Showing page {page}/{total_pages}."
    show_message(msg, "blue")
    return papers


def get_reading_list_papers() -> List[Paper]:
    items = _load_reading_list()
    return [Paper(**item) for item in items]


def read_reading_list(indices: List[int]):
    items = _load_reading_list()
    if not items:
        show_error("Reading list is empty.")
        return

    found = 0
    for idx in indices:
        if idx < 1 or idx > len(items):
            show_error(f"Invalid index: {idx} (reading list has {len(items)} papers)")
            continue
        paper = Paper(**items[idx - 1])
        show_paper_detail(paper)
        found += 1

    if found == 0:
        show_message("No valid indices provided.", "yellow")
