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
app = FastAPI(title="JOB-AUTOMATION API", version="1.2.0")
origins=[x.strip() for x in os.getenv("CORS_ORIGINS","*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.mount("/static",StaticFiles(directory=BASE/"static"),name="static")

def db():
    url=os.getenv("DATABASE_URL")
    return JobRepository(url) if url else None

def require_db():
    repo=db()
    if repo is None: raise HTTPException(503,"DATABASE_URL is not configured")
    repo.init(); return repo

@app.get("/",include_in_schema=False)
def root(): return FileResponse(BASE/"index.html")

@app.get("/api")
def api_info()->dict[str,Any]: return {"name":"JOB-AUTOMATION API","status":"ok","timestamp":datetime.now(timezone.utc).isoformat()}

@app.get("/health")
def health():
    repo=db()
    if repo is None: return {"status":"ok","database":"not_configured"}
    try: repo.init(); return {"status":"ok","database":"connected","counts":dict(repo.counts())}
    except Exception as exc: return {"status":"degraded","database":"error","error":type(exc).__name__}

@app.get("/api/stats")
def stats(): return dict(require_db().counts())

@app.get("/api/jobs")
def jobs(limit:int=50,min_score:int=0):
    return [dict(row) for row in require_db().top(max(1,min(limit,100)),max(0,min_score))]

@app.get("/api/expiring")
def expiring(hours:int=72): return [dict(row) for row in require_db().expiring(max(1,min(hours,720)))]

@app.get("/api/applications")
def applications(limit:int=100):
    return [dict(row) for row in require_db().applications(max(1,min(limit,100)))]

@app.patch("/api/applications/{application_id}")
def update_application(application_id:int,payload:dict[str,Any]):
    status=payload.get("status")
    if not status: raise HTTPException(400,"status is required")
    try: require_db().update_application_status(application_id,status)
    except ValueError as exc: raise HTTPException(400,str(exc))
    return {"status":"updated","application_id":application_id,"new_status":status}

@app.get("/api/rag/status")
def rag_status():
    with require_db().conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS rag_documents (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, chunks INTEGER DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW())")
        count=c.execute("SELECT COALESCE(SUM(chunks),0) AS chunks, COUNT(*) AS documents FROM rag_documents").fetchone()
        c.commit()
    configured=bool(os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_MODEL"))
    return {"configured":configured,"documents":count["documents"],"chunks":count["chunks"],"message":f"{count['documents']} document(s) · {count['chunks']} chunk(s) indexed" if count["documents"] else "Knowledge base is ready for CV ingestion"}

@app.post("/api/hunt")
def hunt():
    try:
        from job_agent.pipeline import run
        ranked=run()
        return {"status":"completed","discovered":len(ranked),"strong_matches":sum(1 for x in ranked if x[0]>=85),"message":"Job hunt completed and jobs were saved to Neon"}
    except Exception as exc:
        raise HTTPException(500,f"Job hunt failed: {type(exc).__name__}: {exc}")
