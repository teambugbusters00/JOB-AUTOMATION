from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    title: str
    company: str
    location: str
    remote: str
    url: str
    source: str
    description: str = ""
    salary: Optional[str] = None


def normalize(job: Job) -> Job:
    job.title = " ".join(job.title.split())
    job.company = " ".join(job.company.split())
    return job


def dedupe(jobs):
    seen = set()
    out = []
    for job in jobs:
        key = (job.company.lower(), job.title.lower(), job.url.split("?")[0])
        if key not in seen:
            seen.add(key)
            out.append(job)
    return out


def india_eligible(job: Job) -> bool:
    text = f"{job.location} {job.remote} {job.description}".lower()
    positive = ["india", "worldwide", "everywhere", "anywhere", "global", "remote - india", "remote india"]
    negative = ["us only", "usa only", "united states only", "work authorization required in the us", "relocation required"]
    return any(x in text for x in positive) and not any(x in text for x in negative)
