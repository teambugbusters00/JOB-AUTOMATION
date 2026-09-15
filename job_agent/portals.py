from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin
import json
import re
import time
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
    Portal("greenhouse", "Greenhouse", "https://www.greenhouse.com/", "api", "Public company ATS feeds; default board slugs are included and can be overridden with GREENHOUSE_BOARDS."),
    Portal("lever", "Lever", "https://www.lever.co/", "api", "Public company ATS feeds; default company slugs are included and can be overridden with LEVER_SITES."),
    Portal("ashby", "Ashby", "https://www.ashbyhq.com/", "api", "Public Ashby job-board feeds; default boards are included and can be overridden with ASHBY_BOARDS."),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JOB-AUTOMATION/2.2; +https://job-automation-8nm3.onrender.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


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


def _get(url: str, timeout: int = 25) -> requests.Response:
    last = None
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            last = exc
            if attempt < 2:
                time.sleep(0.8 * (attempt + 1))
    raise last or RuntimeError("request failed")


def _xml_items(root: ET.Element):
    # Supports RSS and Atom feeds, including namespaced XML.
    for item in root.iter():
        tag = item.tag.rsplit("}", 1)[-1].lower()
        if tag in {"item", "entry"}:
            yield item


def _xml_text(item: ET.Element, names: tuple[str, ...]) -> str:
    for child in item.iter():
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag in names and (child.text or "").strip():
            return _clean(child.text or "")
    return ""


def _xml_link(item: ET.Element) -> str:
    for child in item.iter():
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag == "link":
            href = child.attrib.get("href") or child.text or ""
            if href.strip(): return href.strip()
    return ""


def collect_startup_jobs(max_per_feed: int = 50) -> list[Job]:
    jobs: list[Job] = []
    feeds = [
        "https://startup.jobs/feeds/jobs?role=engineering",
        "https://startup.jobs/feeds/jobs?role=software",
        "https://startup.jobs/feeds/jobs?role=data",
    ]
    for feed in feeds:
        try:
            root = ET.fromstring(_get(feed, 20).content)
        except (ET.ParseError, requests.RequestException):
            continue
        for item in list(_xml_items(root))[:max_per_feed]:
            title = _xml_text(item, ("title",))
            link = _xml_link(item)
            desc = BeautifulSoup(_xml_text(item, ("description", "summary", "content")), "html.parser").get_text(" ", strip=True)
            if not title or not link: continue
            jobs.append(Job(title=title, company="Startup Jobs", location="Global", remote="remote" if "remote" in (title+desc).lower() else "", url=link, source="Startup Jobs", description=desc, employment_type=_job_type(title+desc)))
    return jobs


def _jsonld_jobs(soup: BeautifulSoup, page_url: str, source: str, limit: int) -> list[Job]:
    out: list[Job] = []
    for node in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(node.string or node.get_text())
        except Exception:
            continue
        candidates = data if isinstance(data, list) else data.get("itemListElement", []) if isinstance(data, dict) else []
        if isinstance(data, dict) and data.get("@type") == "JobPosting": candidates = [data]
        for item in candidates:
            if isinstance(item, dict) and isinstance(item.get("item"), dict): item = item["item"]
            if not isinstance(item, dict) or item.get("@type") != "JobPosting": continue
            title = _clean(str(item.get("title", "")))
            link = urljoin(page_url, str(item.get("url", "")))
            desc = BeautifulSoup(str(item.get("description", "")), "html.parser").get_text(" ", strip=True)
            loc = item.get("jobLocation", {})
            if isinstance(loc, list): loc = loc[0] if loc else {}
            address = loc.get("address", {}) if isinstance(loc, dict) else {}
            location = ", ".join(str(address.get(k, "")) for k in ("addressLocality", "addressRegion", "addressCountry") if address.get(k))
            remote = "remote" if "telecommute" in str(item.get("jobLocationType", "")).lower() or "remote" in (title + desc).lower() else ""
            if title and link: out.append(Job(title, source, location or "Unknown", remote, link, source, desc, employment_type=_job_type(title + desc)))
            if len(out) >= limit: return out
    return out


def collect_public_html(url: str, source: str, limit: int = 80) -> list[Job]:
    r = _get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    out: list[Job] = _jsonld_jobs(soup, url, source, limit)
    seen: set[str] = {j.url for j in out}
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a.get("href"))
        text = _clean(a.get_text(" ", strip=True))
        if not text or len(text) < 4 or len(text) > 220 or href in seen: continue
        low = (text + " " + href).lower()
        path = href.lower()
        if not any(k in low for k in ["job", "engineer", "developer", "intern", "software", "data", "machine learning", "ai", "frontend", "backend", "full-stack"]): continue
        if any(x in path for x in ["login", "signup", "privacy", "terms", "about", "contact"]): continue
        parent = a.parent.get_text(" ", strip=True) if a.parent else text
        context = _clean(parent)
        out.append(Job(title=text, company=source, location="Unknown", remote="remote" if "remote" in context.lower() else "", url=href, source=source, description=context[:2500], employment_type=_job_type(context)))
        seen.add(href)
        if len(out) >= limit: break
    return out


def collect_topstartups(limit: int = 80) -> list[Job]: return collect_public_html("https://topstartups.io/jobs/", "Top Startups", limit)
def collect_thehub(limit: int = 80) -> list[Job]: return collect_public_html("https://thehub.io/jobs", "The Hub", limit)
def collect_workinstartups(limit: int = 80) -> list[Job]: return collect_public_html("https://workinstartups.com/", "Work in Startups", limit)
def collect_startupmap(limit: int = 80) -> list[Job]: return collect_public_html("https://startupmap.one/jobs", "StartupMap", limit)


def collect_public_portals() -> list[Job]:
    jobs: list[Job] = []
    for collector in [collect_startup_jobs, collect_topstartups, collect_thehub, collect_workinstartups, collect_startupmap]:
        try: jobs.extend(collector())
        except Exception as exc: print(f"portal_collector={collector.__name__} failed={type(exc).__name__}")
    return jobs
