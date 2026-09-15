import os
import requests
from bs4 import BeautifulSoup
from ..models import Job


# Public Lever company slugs. Users can override this list with LEVER_SITES.
DEFAULT_SITES = "collate,sonarsource,rippling,webflow"


def collect_lever():
    jobs = []
    sites = [x.strip() for x in os.getenv("LEVER_SITES", DEFAULT_SITES).split(",") if x.strip()]
    for site in sites:
        try:
            r = requests.get(
                f"https://api.lever.co/v0/postings/{site}",
                params={"mode": "json"},
                timeout=20,
                headers={"User-Agent": "JOB-AUTOMATION/1.0"},
            )
            r.raise_for_status()
            items = r.json()
        except (requests.RequestException, ValueError):
            continue
        for x in items:
            desc = BeautifulSoup(x.get("descriptionPlain", x.get("description", "")), "html.parser").get_text(" ", strip=True)
            categories = x.get("categories", {})
            loc = categories.get("location", "")
            jobs.append(Job(x.get("text", ""), site, loc, "remote" if "remote" in loc.lower() else "", x.get("hostedUrl", x.get("applyUrl", "")), "lever", desc, external_id=x.get("id", "")))
    return [j for j in jobs if j.title and j.url]
