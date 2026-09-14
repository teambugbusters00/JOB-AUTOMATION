import re
from html import unescape
import requests
from ..models import Job
from ..portals import collect_public_portals

TIMEOUT = 20
HEADERS = {"User-Agent": "JOB-AUTOMATION/1.0 (+job discovery)"}

def clean_html(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    return " ".join(unescape(text).split())

def wanted(profile=None):
    if not profile: return ["software engineer", "ai engineer", "machine learning", "full stack", "backend", "frontend", "genai", "llm"]
    roles = profile.get("roles") or []
    skills = profile.get("skills") or []
    return list(dict.fromkeys([str(x).strip() for x in (roles[:8] + skills[:8]) if str(x).strip()])) or ["software engineer"]

def matches(job, profile):
    text = f"{job.title} {job.description} {job.location} {job.remote}".lower()
    terms = [x.lower() for x in wanted(profile)]
    return any(x in text for x in terms)

def collect_remotive(profile=None):
    r = requests.get("https://remotive.com/api/remote-jobs", timeout=TIMEOUT, headers=HEADERS); r.raise_for_status()
    jobs=[]
    for x in r.json().get("jobs", []):
        j=Job(title=x.get("title", ""), company=x.get("company_name", "Unknown"), location=x.get("candidate_required_location") or "Remote", remote=x.get("candidate_required_location") or "Worldwide", url=x.get("url", ""), source="Remotive", description=clean_html(x.get("description")), salary=x.get("salary"), employment_type=x.get("job_type", ""), external_id=f"remotive:{x.get('id')}")
        if matches(j,profile): jobs.append(j)
    return jobs

def collect_remoteok(profile=None):
    r=requests.get("https://remoteok.com/api", timeout=TIMEOUT, headers={**HEADERS,"Accept":"application/json"}); r.raise_for_status()
    jobs=[]
    for x in r.json():
        if not isinstance(x,dict) or not x.get("position"): continue
        j=Job(title=x.get("position", ""), company=x.get("company", "Unknown"), location=x.get("location") or "Worldwide", remote="Worldwide", url=x.get("apply_url") or x.get("url") or f"https://remoteok.com/remote-jobs/{x.get('slug','')}", source="Remote OK", description=clean_html(x.get("description")), salary=(f"{x.get('salary_min')} - {x.get('salary_max')}" if x.get('salary_min') or x.get('salary_max') else None), employment_type="", external_id=f"remoteok:{x.get('id')}", tags=x.get("tags") or [])
        if matches(j,profile): jobs.append(j)
    return jobs

def collect_jobicy(profile=None):
    r=requests.get("https://jobicy.com/api/v2/remote-jobs", params={"count":200}, timeout=TIMEOUT, headers=HEADERS); r.raise_for_status()
    jobs=[]
    for x in r.json().get("jobs", []):
        types=x.get("jobType") or []
        j=Job(title=x.get("jobTitle", ""), company=x.get("companyName", "Unknown"), location=x.get("jobGeo") or "Anywhere", remote=x.get("jobGeo") or "Anywhere", url=x.get("url", ""), source="Jobicy", description=clean_html(x.get("jobDescription") or x.get("jobExcerpt")), salary=(f"{x.get('salaryMin')} - {x.get('salaryMax')} {x.get('salaryCurrency','')}" if x.get('salaryMin') or x.get('salaryMax') else None), employment_type=", ".join(types), external_id=f"jobicy:{x.get('id')}", tags=x.get("jobIndustry") or [])
        if matches(j,profile): jobs.append(j)
    return jobs

def collect_arbeitnow(profile=None):
    r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=TIMEOUT, headers=HEADERS); r.raise_for_status()
    data=r.json(); raw=data.get("data", data.get("jobs", [])) if isinstance(data,dict) else data
    jobs=[]
    for x in raw or []:
        j=Job(title=x.get("title", ""), company=x.get("company_name", "Unknown"), location=x.get("location") or "Remote", remote=str(x.get("remote", "")), url=x.get("url", ""), source="Arbeitnow", description=clean_html(x.get("description")), employment_type=", ".join(x.get("job_types") or []), external_id=f"arbeitnow:{x.get('slug') or x.get('url')}", tags=x.get("tags") or [])
        if matches(j,profile): jobs.append(j)
    return jobs

def collect_public_boards(profile=None):
    out=[]
    for collector in (collect_remotive, collect_remoteok, collect_jobicy, collect_arbeitnow):
        try: out.extend(collector(profile))
        except Exception as exc: print(f"collector={collector.__name__} failed: {type(exc).__name__}")
    try:
        portal_jobs=collect_public_portals()
        out.extend([j for j in portal_jobs if matches(j,profile)])
    except Exception as exc:
        print(f"collector=multi_startup_portals failed: {type(exc).__name__}")
    return out
