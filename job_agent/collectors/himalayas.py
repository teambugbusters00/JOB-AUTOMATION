import os
import requests
from ..models import Job

API = "https://himalayas.app/api/search"


def collect_himalayas():
    jobs = []
    keywords = os.getenv("JOB_KEYWORDS", "software engineer,ai engineer,machine learning,full stack,backend,frontend,genai,llm,ai agent,research intern").split(",")
    for keyword in keywords:
        params = {"q": keyword.strip(), "country": "India", "page": 1, "limit": 20}
        try:
            r = requests.get(API, params=params, timeout=25, headers={"User-Agent": "JOB-AUTOMATION/1.0"})
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError):
            continue
        items = data.get("jobs", data if isinstance(data, list) else [])
        for x in items:
            jobs.append(Job(
                title=x.get("title", "").strip(), company=x.get("companyName", x.get("company", "")).strip(),
                location=x.get("location", "India"), remote=x.get("remote", ""),
                url=x.get("applicationUrl") or x.get("url", ""), source="himalayas",
                description=x.get("description", ""), salary=x.get("salary")
            ))
    return [j for j in jobs if j.title and j.url]
