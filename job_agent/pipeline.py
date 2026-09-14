import os
from .models import dedupe, india_eligible, normalize
from .matcher import score, explain, score_with_profile, explain_with_profile
from .collectors import collect_himalayas, collect_greenhouse, collect_lever, collect_ashby
from .collectors.public_boards import collect_public_boards
from .database import JobRepository
from .notifications import send_telegram


def collect_all(profile=None):
    jobs=[]
    for collector in [collect_himalayas, collect_greenhouse, collect_lever, collect_ashby]:
        try: jobs.extend(collector())
        except Exception as exc: print(f"collector={collector.__name__} failed: {type(exc).__name__}")
    jobs.extend(collect_public_boards(profile))
    return [normalize(j) for j in jobs]

def profile_eligible(job, profile):
    if not profile: return india_eligible(job)
    if profile.get("india_eligibility_required", True) and not india_eligible(job): return False
    modes=[str(x).lower() for x in profile.get("employment_modes",[])]
    if modes:
        text=f"{job.title} {job.employment_type} {job.description}".lower()
        if not any(m in text for m in modes):
            if not ("full-time" in modes and "full_time" in job.employment_type.lower()) and not ("internship" in modes and "intern" in text): return False
    return True

def _report(ranked,total,eligible,queued=0):
    strong=[x for x in ranked if x[0]>=85]
    lines=["JOB AUTOMATION — DAILY REPORT","────────────────────────────",f"Discovered: {total}",f"Eligible: {eligible}",f"Strong matches (85+): {len(strong)}",f"Application review queue: {queued}","","TOP MATCHES"]
    for s,job,reasons in ranked[:10]:
        lines += [f"{s}% | {job.company} | {job.title}",f"     {job.location} | {job.source}",f"     ✓ {', '.join(reasons[:6])}" if reasons else "",f"     {job.url}"]
    return "\n".join(lines)

def run(profile=None, user_id=None):
    raw=collect_all(profile)
    eligible=[j for j in raw if profile_eligible(j,profile)]
    jobs=dedupe(eligible)
    scorer=(lambda j: score_with_profile(j,profile)) if profile else score
    explainer=(lambda j: explain_with_profile(j,profile)) if profile else explain
    ranked=sorted(((scorer(j),j,explainer(j)) for j in jobs),key=lambda x:x[0],reverse=True)
    queued=0
    db_url=os.getenv("DATABASE_URL")
    if db_url:
        repo=JobRepository(db_url); repo.init()
        for s,job,reasons in ranked:
            job_id=repo.upsert(job,s,reasons)
            if s>=85:
                repo.queue_application(job_id,resume_variant=_resume_variant(job),user_id=user_id)
                queued+=1
    report=_report(ranked,len(raw),len(eligible),queued); print(report)
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"): send_telegram(report[:3900])
    return ranked

def _resume_variant(job):
    text=f"{job.title} {job.description}".lower()
    if any(x in text for x in ["llm","rag","generative ai","genai","agentic"]): return "genai-llm"
    if any(x in text for x in ["machine learning","ml engineer","pytorch","tensorflow","computer vision","nlp"]): return "ai-ml"
    if any(x in text for x in ["backend","fastapi","flask","node.js","nodejs"]): return "backend"
    if any(x in text for x in ["react","frontend","full stack","fullstack","next.js"]): return "full-stack"
    return "software-engineering"
