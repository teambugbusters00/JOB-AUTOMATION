from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin
import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .models import Job


@dataclass(frozen=True)
class Portal:
    key: str
    name: str
    url: str
    mode: str
    description: str
    enabled: bool = True


PORTALS = [
    Portal("himalayas", "Himalayas", "https://himalayas.app/jobs", "api", "Remote jobs with a public jobs API."),
    Portal("startup_jobs", "Startup Jobs", "https://startup.jobs/", "rss", "Startup jobs with a public RSS feed; API key can be added later."),
    Portal("topstartups", "Top Startups", "https://topstartups.io/jobs/", "html", "Startup jobs with public searchable pages."),
    Portal("thehub", "The Hub", "https://thehub.io/jobs", "html", "Nordic startup and remote jobs."),
    Portal("workinstartups", "Work in Startups", "https://workinstartups.com/", "html", "UK startup jobs."),
    Portal("startupmap", "StartupMap", "https://startupmap.one/jobs", "html", "European startup jobs, updated from company career pages."),
    Portal("welcometothejungle", "Welcome to the Jungle", "https://www.welcometothejungle.com/en/jobs", "link", "Profile-driven global startup and tech jobs; open the portal to use its native matching."),
    Portal("wellfound", "Wellfound", "https://wellfound.com/jobs", "link", "Startup jobs; native account/search experience is used instead of unauthorized automated scraping."),
    Portal("greenhouse", "Greenhouse", "https://www.greenhouse.com/", "api", "Company ATS feeds configured through GREENHOUSE_BOARDS."),
    Portal("lever", "Lever", "https://www.lever.co/", "api", "Company ATS feeds configured through LEVER_SITES."),
    Portal("ashby", "Ashby", "https://www.ashbyhq.com/", "api", "Company ATS feeds configured through ASHBY_BOARDS."),
]


def portal_cards() -> list[dict]:
    return [p.__dict__ for p in PORTALS]


def _clean(text: str) -> str:
    return " ".join((text or "").split())


def _job_type(text: str) -> str:
    low = text.lower()
    if "intern" in low: return "internship"
    if "part-time" in low or "part time" in low: return "part-time"
    if "contract" in low: return "contract"
    return "full-time"


def collect_startup_jobs(max_per_feed: int = 50) -> list[Job]:
    jobs: list[Job] = []
    feeds = [
        "https://startup.jobs/feeds/jobs?role=engineering",
        "https://startup.jobs/feeds/jobs?role=software",
        "https://startup.jobs/feeds/jobs?role=data",
    ]
    for feed in feeds:
        r = requests.get(feed, timeout=20, headers={"User-Agent": "JOB-AUTOMATION/1.0"})
        r.raise_for_status()
        root = ET.fromstring(r.text)
        for item in root.findall(".//item")[:max_per_feed]:
            title = _clean(item.findtext("title", ""))
            link = _clean(item.findtext("link", ""))
            desc = BeautifulSoup(item.findtext("description", ""), "html.parser").get_text(" ", strip=True)
            if not title or not link: continue
            jobs.append(Job(title=title, company="Startup Jobs", location="Global", remote="remote" if "remote" in (title+desc).lower() else "", url=link, source="Startup Jobs", description=desc, employment_type=_job_type(title+desc)))
    return jobs


def collect_public_html(url: str, source: str, limit: int = 80) -> list[Job]:
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0 JOB-AUTOMATION/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out: list[Job] = []
    seen: set[str] = set()
    # Generic, conservative extraction: only public anchor content, no login/session automation.
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a.get("href"))
        text = _clean(a.get_text(" ", strip=True))
        if not text or len(text) < 5 or len(text) > 180: continue
        if href in seen: continue
        low = (text + " " + href).lower()
        if not any(k in low for k in ["job", "engineer", "developer", "intern", "software", "data", "machine learning", "ai"]): continue
        if any(x in href.lower() for x in ["login", "signup", "privacy", "terms", "about", "contact"]): continue
        parent = a.parent.get_text(" ", strip=True) if a.parent else text
        context = _clean(parent)
        company = source
        # Common "Title Company Location" patterns are kept in description/context rather than guessed aggressively.
        out.append(Job(title=text, company=company, location="Unknown", remote="remote" if "remote" in context.lower() else "", url=href, source=source, description=context[:2500], employment_type=_job_type(context)))
        seen.add(href)
        if len(out) >= limit: break
    return out


def collect_topstartups(limit: int = 80) -> list[Job]:
    return collect_public_html("https://topstartups.io/jobs/", "Top Startups", limit)


def collect_thehub(limit: int = 80) -> list[Job]:
    return collect_public_html("https://thehub.io/jobs", "The Hub", limit)


def collect_workinstartups(limit: int = 80) -> list[Job]:
    return collect_public_html("https://workinstartups.com/", "Work in Startups", limit)


def collect_startupmap(limit: int = 80) -> list[Job]:
    return collect_public_html("https://startupmap.one/jobs", "StartupMap", limit)


def collect_public_portals() -> list[Job]:
    jobs: list[Job] = []
    collectors = [collect_startup_jobs, collect_topstartups, collect_thehub, collect_workinstartups, collect_startupmap]
    for collector in collectors:
        try:
            jobs.extend(collector())
        except Exception as exc:
            print(f"portal_collector={collector.__name__} failed={type(exc).__name__}")
    # Generic HTML extraction can repeat the same links; normal pipeline dedupe handles that.
    return jobs
