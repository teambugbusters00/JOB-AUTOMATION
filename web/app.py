import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from job_agent.database.repository import JobRepository

app = FastAPI(title="JOB-AUTOMATION API", version="1.0.0")

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def db() -> JobRepository | None:
    url = os.getenv("DATABASE_URL")
    return JobRepository(url) if url else None


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "JOB-AUTOMATION API",
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health() -> dict[str, Any]:
    repo = db()
    if repo is None:
        return {"status": "ok", "database": "not_configured"}
    try:
        repo.init()
        counts = repo.counts()
        return {"status": "ok", "database": "connected", "counts": dict(counts)}
    except Exception as exc:
        return {"status": "degraded", "database": "error", "error": type(exc).__name__}


@app.get("/api/jobs")
def jobs(limit: int = 20) -> list[dict[str, Any]]:
    repo = db()
    if repo is None:
        return []
    return [dict(row) for row in repo.top(max(1, min(limit, 100)))]


@app.get("/api/expiring")
def expiring(hours: int = 72) -> list[dict[str, Any]]:
    repo = db()
    if repo is None:
        return []
    return [dict(row) for row in repo.expiring(max(1, min(hours, 720)))]
