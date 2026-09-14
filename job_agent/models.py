from dataclasses import dataclass, field
from typing import Optional
import hashlib
import re


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
    employment_type: str = ""
    deadline: Optional[object] = None
    external_id: str = ""
    posted_at: Optional[object] = None
    tags: list[str] = field(default_factory=list)

    @property
    def fingerprint(self) -> str:
        raw = "|".join([
            re.sub(r"\W+", " ", self.company.lower()).strip(),
            re.sub(r"\W+", " ", self.title.lower()).strip(),
            re.sub(r"\W+", " ", self.location.lower()).strip(),
            self.employment_type.lower().strip(),
        ])
        return hashlib.sha256(raw.encode()).hexdigest()


def normalize(job: Job) -> Job:
    job.title = " ".join(job.title.split())
    job.company = " ".join(job.company.split())
    job.location = " ".join(job.location.split())
    job.description = " ".join(job.description.split())
    return job


def dedupe(jobs):
    seen = set()
    out = []
    for job in jobs:
        key = job.external_id or job.fingerprint
        if key not in seen:
            seen.add(key)
            out.append(job)
    return out


def india_eligible(job: Job) -> bool:
    text = f"{job.location} {job.remote} {job.description}".lower()
    positive = ["india", "worldwide", "everywhere", "anywhere", "global", "remote - india", "remote india"]
    negative = [
        "us only", "usa only", "united states only", "u.s. only",
        "work authorization required in the us", "must be authorized to work in the us",
        "relocation required", "uk only", "canada only", "europe only",
    ]
    return any(x in text for x in positive) and not any(x in text for x in negative)
