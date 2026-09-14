import os
import requests
from bs4 import BeautifulSoup
from ..models import Job


def collect_ashby():
    jobs = []
    boards = [x.strip() for x in os.getenv("ASHBY_BOARDS", "").split(",") if x.strip()]
    for board in boards:
        try:
            r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{board}", timeout=20)
            r.raise_for_status()
            items = r.json().get("jobs", [])
        except (requests.RequestException, ValueError):
            continue
        for x in items:
            desc = BeautifulSoup(x.get("descriptionHtml", x.get("descriptionPlain", "")), "html.parser").get_text(" ", strip=True)
            locs = x.get("location", "")
            if isinstance(locs, list):
                locs = ", ".join(str(v) for v in locs)
            jobs.append(Job(x.get("title", ""), board, str(locs), "remote" if "remote" in str(locs).lower() else "", x.get("jobUrl", x.get("applyUrl", "")), "ashby", desc, external_id=x.get("jobUrl", "")))
    return [j for j in jobs if j.title and j.url]
