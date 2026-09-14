import os
from .models import dedupe, india_eligible, normalize
from .matcher import score, explain
from .collectors import collect_himalayas, collect_greenhouse, collect_lever, collect_ashby
from .database import JobRepository
from .notifications import send_telegram


def collect_all():
    jobs = []
    for collector in [collect_himalayas, collect_greenhouse, collect_lever, collect_ashby]:
        try:
            jobs.extend(collector())
        except Exception as exc:
            print(f"collector={collector.__name__} failed: {type(exc).__name__}")
    return [normalize(j) for j in jobs]


def _report(ranked, total, eligible, queued=0):
    strong = [x for x in ranked if x[0] >= 85]
    lines = [
        "JOB AUTOMATION — DAILY REPORT",
        "────────────────────────────",
        f"Discovered: {total}",
        f"India eligible: {eligible}",
        f"Strong matches (85+): {len(strong)}",
        f"Application review queue: {queued}",
        "",
        "TOP MATCHES",
    ]
    for s, job, reasons in ranked[:10]:
        lines.append(f"{s}% | {job.company} | {job.title}")
        lines.append(f"     {job.location} | {job.source}")
        if reasons:
            lines.append(f"     ✓ {', '.join(reasons[:6])}")
        lines.append(f"     {job.url}")
    return "\n".join(lines)


def run():
    raw = collect_all()
    eligible = [j for j in raw if india_eligible(j)]
    jobs = dedupe(eligible)
    ranked = sorted(((score(j), j, explain(j)) for j in jobs), key=lambda x: x[0], reverse=True)

    queued = 0
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        repo = JobRepository(db_url)
        repo.init()
        for s, job, reasons in ranked:
            job_id = repo.upsert(job, s, reasons)
            if s >= 85:
                # Preparation is automatic; submission remains human-approved.
                repo.queue_application(job_id, resume_variant=_resume_variant(job))
                queued += 1

    report = _report(ranked, len(raw), len(eligible), queued)
    print(report)
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        send_telegram(report[:3900])
    return ranked


def _resume_variant(job):
    text = f"{job.title} {job.description}".lower()
    if any(x in text for x in ["llm", "rag", "generative ai", "genai", "agentic"]):
        return "genai-llm"
    if any(x in text for x in ["machine learning", "ml engineer", "pytorch", "tensorflow", "computer vision", "nlp"]):
        return "ai-ml"
    if any(x in text for x in ["backend", "fastapi", "flask", "node.js", "nodejs"]):
        return "backend"
    if any(x in text for x in ["react", "frontend", "full stack", "fullstack", "next.js"]):
        return "full-stack"
    return "software-engineering"
