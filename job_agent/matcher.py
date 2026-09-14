from pathlib import Path
import re
import yaml
from .models import Job

ROOT = Path(__file__).resolve().parents[1]
PROFILE = yaml.safe_load((ROOT / 'config' / 'profile.yaml').read_text())

ROLE_TERMS = [x.lower() for x in PROFILE['roles']]
SKILLS = [x.lower() for x in PROFILE['skills']]

def score(job: Job) -> int:
    text = f"{job.title} {job.description}".lower()
    role = min(45, sum(8 for r in ROLE_TERMS if r in text))
    skills = min(40, sum(3 for s in SKILLS if s in text))
    location = 15 if any(x in text for x in ['india', 'worldwide', 'everywhere', 'anywhere', 'global']) else 0
    return min(100, role + skills + location)

def explain(job: Job) -> list[str]:
    text = f"{job.title} {job.description}".lower()
    return [s for s in PROFILE['skills'] if s.lower() in text][:10]
