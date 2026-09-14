from .models import Job, dedupe, india_eligible
from .matcher import score, explain

# Portal adapters can be added here as compliant public-page collectors.
def collect_all():
    return []

def run():
    jobs = [j for j in collect_all() if india_eligible(j)]
    jobs = dedupe(jobs)
    ranked = sorted(((score(j), j, explain(j)) for j in jobs), key=lambda x: x[0], reverse=True)
    for s, job, matched in ranked[:20]:
        print(f"{s:3} | {job.company} | {job.title} | {job.location} | {job.url}")
        if matched:
            print("     match:", ", ".join(matched))
    return ranked
