import os
import requests
from bs4 import BeautifulSoup
from ..models import Job


def collect_greenhouse():
    jobs = []
    boards = [x.strip() for x in os.getenv("GREENHOUSE_BOARDS", "").split(",") if x.strip()]
    for board in boards:
        try:
            r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", params={"content": "true"}, timeout=20)
            r.raise_for_status()
            items = r.json().get("jobs", [])
        except (requests.RequestException, ValueError):
            continue
        for x in items:
            desc = BeautifulSoup(x.get("content", ""), "html.parser").get_text(" ", strip=True)
            loc = (x.get("location") or {}).get("name", "")
            jobs.append(Job(x.get("title", ""), board, loc, "remote" if "remote" in loc.lower() else "", x.get("absolute_url", ""), "greenhouse", desc, external_id=str(x.get("id", ""))))
    return [j for j in jobs if j.title and j.url]
