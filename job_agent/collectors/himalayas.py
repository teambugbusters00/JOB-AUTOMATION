import os
import requests
from bs4 import BeautifulSoup
from ..models import Job

API = "https://himalayas.app/jobs/api/search"


def collect_himalayas():
    jobs = []
    keywords = os.getenv(
        "JOB_KEYWORDS",
        "software engineer,ai engineer,machine learning,full stack,backend,frontend,genai,llm,ai agent,research intern",
    ).split(",")
    for keyword in keywords:
        params = {
            "q": keyword.strip(),
            "country": "India",
            "sort": "recent",
            "page": 1,
        }
        try:
            r = requests.get(API, params=params, timeout=25, headers={"User-Agent": "JOB-AUTOMATION/1.0"})
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError):
            continue
        for x in data.get("jobs", []):
            restrictions = x.get("locationRestrictions") or []
            location = ", ".join(restrictions) if restrictions else "Worldwide"
            remote = "worldwide" if not restrictions else "India"
            description = BeautifulSoup(x.get("description", ""), "html.parser").get_text(" ", strip=True)
            salary = None
            if x.get("minSalary") is not None or x.get("maxSalary") is not None:
                salary = f"{x.get('currency', '')} {x.get('minSalary', '')}-{x.get('maxSalary', '')} / {x.get('salaryPeriod', 'annual')}"
            jobs.append(Job(
                title=x.get("title", "").strip(),
                company=x.get("companyName", "").strip(),
                location=location,
                remote=remote,
                url=x.get("applicationLink", ""),
                source="himalayas",
                description=description,
                salary=salary,
                employment_type=x.get("employmentType", ""),
                deadline=x.get("expiryDate"),
                external_id=x.get("guid", ""),
            ))
    return [j for j in jobs if j.title and j.url]
