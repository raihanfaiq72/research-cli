from typing import Optional
import requests
from config import settings
from models.paper import Paper
from utils.cache import get_cache, set_cache


class UnpaywallService:
    BASE_URL = "https://api.unpaywall.org/v2"

    def __init__(self):
        self.email = settings.unpaywall_email
        self.timeout = settings.request_timeout

    def find_pdf(self, doi: str) -> Optional[Paper]:
        if not self.email:
            return None

        cache_key = f"pdf_{doi}"
        cached = get_cache("unpaywall", cache_key)
        if cached:
            return Paper(**cached)

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        try:
            response = requests.get(
                f"{self.BASE_URL}/{doi_clean}",
                params={"email": self.email},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            oa_location = data.get("best_oa_location") or {}
            pdf_url = oa_location.get("url_for_pdf") or oa_location.get("url")

            paper = Paper(
                title=data.get("title", "Untitled"),
                doi=data.get("doi"),
                year=data.get("year"),
                open_access=data.get("is_oa", False),
                pdf_url=pdf_url,
                source="unpaywall",
                journal=data.get("journal_name"),
                publisher=data.get("publisher"),
            )

            authors = [
                a.get("family", "") for a in data.get("z_authors", []) if a.get("family")
            ]
            if authors:
                paper.authors = authors

            set_cache("unpaywall", cache_key, paper.model_dump())
            return paper
        except requests.RequestException:
            return None
