from pathlib import Path
import yaml
from .models import Job

ROOT = Path(__file__).resolve().parents[1]
PROFILE = yaml.safe_load((ROOT / "config" / "profile.yaml").read_text())
ROLE_TERMS = [x.lower() for x in PROFILE["roles"]]
SKILLS = [x.lower() for x in PROFILE["skills"]]


def _text(job):
    return f"{job.title} {job.description} {job.location} {job.remote} {job.employment_type}".lower()


def score(job: Job) -> int:
    text = _text(job)
    role_hits = sum(1 for r in ROLE_TERMS if r in text)
    skill_hits = sum(1 for s in SKILLS if s in text)
    role = min(30, role_hits * 5)
    skills = min(35, skill_hits * 2)
    eligibility = 15 if any(x in text for x in ["india", "worldwide", "everywhere", "anywhere", "global"]) else 0
    student = 10 if any(x in text for x in ["intern", "student", "entry-level", "graduate", "0-1 year", "0–1 year"]) else 0
    stack_fit = 10 if any(x in text for x in ["python", "typescript", "react", "fastapi", "pytorch", "llm", "rag", "machine learning"]) else 0
    return min(100, role + skills + eligibility + student + stack_fit)


def explain(job: Job) -> list[str]:
    text = _text(job)
    return [s for s in PROFILE["skills"] if s.lower() in text][:10]
