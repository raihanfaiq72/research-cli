import json
import os
from typing import List, Optional
from models.paper import Paper
from utils.console import console, show_search_results, show_message, show_error, confirm_action
from config import settings


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


def list_reading_list():
    items = _load_reading_list()
    if not items:
        show_message("Reading list is empty.", "yellow")
        return []

    papers = [Paper(**item) for item in items]
    show_search_results(papers, "Reading List")
    return papers


def get_reading_list_papers() -> List[Paper]:
    items = _load_reading_list()
    return [Paper(**item) for item in items]
