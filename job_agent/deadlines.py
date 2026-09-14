import os
from .database import JobRepository
from .notifications import send_telegram


def run(hours=72):
    repo = JobRepository(os.environ["DATABASE_URL"])
    repo.init()
    jobs = repo.expiring(hours)
    if not jobs:
        print(f"No deadlines in the next {hours} hours.")
        return
    lines = [f"JOB DEADLINE ALERT — NEXT {hours} HOURS", ""]
    for j in jobs:
        lines.append(f"{j['company']} | {j['title']} | score {j['score']}")
        lines.append(f"Deadline: {j['deadline']}")
        lines.append(j['url'])
        lines.append("")
    message = "\n".join(lines)
    print(message)
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        send_telegram(message[:3900])


if __name__ == "__main__":
    run()
