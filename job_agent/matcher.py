from pathlib import Path
import yaml
from .models import Job

ROOT = Path(__file__).resolve().parents[1]
PROFILE = yaml.safe_load((ROOT / "config" / "profile.yaml").read_text())

def _text(job): return f"{job.title} {job.description} {job.location} {job.remote} {job.employment_type}".lower()

def score_with_profile(job: Job, profile: dict) -> int:
    text=_text(job)
    roles=[str(x).lower() for x in profile.get("roles",[])]
    skills=[str(x).lower() for x in profile.get("skills",[])]
    role_hits=sum(1 for r in roles if r in text)
    skill_hits=sum(1 for s in skills if s in text)
    role=min(30,role_hits*5); skill=min(35,skill_hits*2)
    eligibility=15 if any(x in text for x in ["india","worldwide","everywhere","anywhere","global","remote"]) else 0
    student=10 if any(x in text for x in ["intern","student","entry-level","graduate","0-1 year","0–1 year"]) else 0
    stack=10 if any(x in text for x in skills[:20] + ["python","typescript","react","fastapi","pytorch","llm","rag","machine learning"]) else 0
    return min(100,role+skill+eligibility+student+stack)

def explain_with_profile(job: Job, profile: dict) -> list[str]:
    text=_text(job)
    return [str(s) for s in profile.get("skills",[]) if str(s).lower() in text][:10]

def score(job: Job) -> int: return score_with_profile(job,PROFILE)
def explain(job: Job) -> list[str]: return explain_with_profile(job,PROFILE)
