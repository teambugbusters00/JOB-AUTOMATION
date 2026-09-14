import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from job_agent.database.repository import JobRepository

BASE = Path(__file__).resolve().parent
app = FastAPI(title="JOB-AUTOMATION API", version="1.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

def db() -> JobRepository | None:
    url = os.getenv("DATABASE_URL")
    return JobRepository(url) if url else None

def require_db() -> JobRepository:
    repo = db()
    if repo is None:
        raise HTTPException(503, "DATABASE_URL is not configured")
    repo.init()
    return repo

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(BASE / "index.html")

@app.get("/api")
def api_info() -> dict[str, Any]:
    return {"name": "JOB-AUTOMATION API", "status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/health")
def health() -> dict[str, Any]:
    repo = db()
    if repo is None:
        return {"status": "ok", "database": "not_configured"}
    try:
        repo.init(); return {"status": "ok", "database": "connected", "counts": dict(repo.counts())}
    except Exception as exc:
        return {"status": "degraded", "database": "error", "error": type(exc).__name__}

@app.get("/api/stats")
def stats():
    return dict(require_db().counts())

@app.get("/api/jobs")
def jobs(limit: int = 20):
    return [dict(row) for row in require_db().top(max(1, min(limit, 100)))]

@app.get("/api/expiring")
def expiring(hours: int = 72):
    return [dict(row) for row in require_db().expiring(max(1, min(hours, 720)))]

@app.post("/api/hunt")
def hunt():
    try:
        from job_agent.pipeline import run
        return {"status": "completed", "result": run()}
    except Exception as exc:
        raise HTTPException(500, f"Job hunt failed: {type(exc).__name__}")
