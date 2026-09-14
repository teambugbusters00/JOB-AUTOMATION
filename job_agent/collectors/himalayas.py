import os
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from ..models import Job

API = "https://himalayas.app/jobs/api/search"


def _ts(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    return value


def _fetch(params):
    try:
        r = requests.get(API, params=params, timeout=25, headers={"User-Agent": "JOB-AUTOMATION/1.0"})
        r.raise_for_status()
        return r.json().get("jobs", [])
    except (requests.RequestException, ValueError):
        return []


def collect_himalayas():
    jobs = []
    keywords = os.getenv("JOB_KEYWORDS", "software engineer,software engineer intern,ai engineer,ai/ml intern,machine learning,full stack,backend,frontend,genai,llm,ai agent,research intern").split(",")
    for keyword in keywords:
        base = {"q": keyword.strip(), "sort": "recent", "page": 1}
        # Two searches ensure both India-specific and worldwide-friendly roles are covered.
        for params in ({**base, "country": "India"}, {**base, "worldwide": "true"}):
            for x in _fetch(params):
                restrictions = x.get("locationRestrictions") or []
                location = ", ".join(restrictions) if restrictions else "Worldwide"
                remote = "worldwide" if not restrictions else "India"
                description = BeautifulSoup(x.get("description", ""), "html.parser").get_text(" ", strip=True)
                salary = None
                if x.get("minSalary") is not None or x.get("maxSalary") is not None:
                    salary = f"{x.get('currency', '')} {x.get('minSalary', '')}-{x.get('maxSalary', '')} / {x.get('salaryPeriod', 'annual')}"
                jobs.append(Job(
                    title=x.get("title", "").strip(), company=x.get("companyName", "").strip(),
                    location=location, remote=remote, url=x.get("applicationLink", ""), source="himalayas",
                    description=description, salary=salary, employment_type=x.get("employmentType", ""),
                    deadline=_ts(x.get("expiryDate")), posted_at=_ts(x.get("pubDate")), external_id=x.get("guid", ""),
                ))
    return [j for j in jobs if j.title and j.url]
