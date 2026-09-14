import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from job_agent.database.repository import JobRepository
from job_agent.portals import PORTALS, portal_cards, collect_startup_jobs, collect_topstartups, collect_thehub, collect_workinstartups, collect_startupmap
from job_agent.collectors import collect_himalayas, collect_greenhouse, collect_lever, collect_ashby
from job_agent.matcher import score_with_profile, explain_with_profile
from job_agent.models import dedupe, india_eligible, normalize
from .security import SESSION_COOKIE, hash_password, verify_password, new_session

BASE = Path(__file__).resolve().parent
app = FastAPI(title="JOB-AUTOMATION API", version="2.0.1")
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

def current_user(session: str|None):
    if not session: raise HTTPException(401,"Login required")
    user=require_db().session_user(hashlib.sha256(session.encode()).hexdigest())
    if not user: raise HTTPException(401,"Session expired. Please log in again.")
    return user

def public_user(user): return {"id":user["id"],"email":user["email"],"created_at":user.get("created_at"),"last_login_at":user.get("last_login_at")}

@app.get("/",include_in_schema=False)
def root(): return FileResponse(BASE/"index.html")
@app.get("/api")
def api_info()->dict[str,Any]: return {"name":"JOB-AUTOMATION API","status":"ok","timestamp":datetime.now(timezone.utc).isoformat()}
@app.get("/health")
def health():
    repo=db()
    if repo is None:return {"status":"ok","database":"not_configured"}
    try:repo.init();return {"status":"ok","database":"connected","counts":dict(repo.counts())}
    except Exception as exc:return {"status":"degraded","database":"error","error":type(exc).__name__}

@app.post("/api/auth/register")
def register(payload:dict[str,Any],response:Response):
    email=str(payload.get("email","")).strip().lower(); password=str(payload.get("password",""))
    if "@" not in email:raise HTTPException(400,"Enter a valid email")
    try:ph=hash_password(password)
    except ValueError as exc:raise HTTPException(400,str(exc))
    repo=require_db()
    try:user=repo.create_user(email,ph)
    except Exception as exc:raise HTTPException(409,"An account with that email already exists") from exc
    token,token_hash,expires=new_session();repo.create_session(user["id"],token_hash,expires)
    response.set_cookie(SESSION_COOKIE,token,max_age=14*24*3600,httponly=True,samesite="lax",secure=os.getenv("ENVIRONMENT","production")=="production",path="/")
    return {"user":public_user(user),"profile":repo.get_profile(user["id"])}

@app.post("/api/auth/login")
def login(payload:dict[str,Any],response:Response):
    email=str(payload.get("email","")).strip().lower();password=str(payload.get("password",""));repo=require_db();user=repo.get_user_by_email(email)
    if not user or not verify_password(password,user["password_hash"]):raise HTTPException(401,"Invalid email or password")
    repo.set_login(user["id"]);token,token_hash,expires=new_session();repo.create_session(user["id"],token_hash,expires);response.set_cookie(SESSION_COOKIE,token,max_age=14*24*3600,httponly=True,samesite="lax",secure=os.getenv("ENVIRONMENT","production")=="production",path="/")
    user=repo.get_user(user["id"]);return {"user":public_user(user),"profile":repo.get_profile(user["id"])}

@app.post("/api/auth/logout")
def logout(response:Response,job_session:str|None=Cookie(default=None)):
    if job_session:require_db().delete_session(hashlib.sha256(job_session.encode()).hexdigest())
    response.delete_cookie(SESSION_COOKIE,path="/");return {"status":"logged_out"}
@app.get("/api/auth/me")
def me(job_session:str|None=Cookie(default=None)):
    user=current_user(job_session);repo=require_db();return {"user":public_user(user),"profile":repo.get_profile(user["id"])}
@app.get("/api/profile")
def get_profile(job_session:str|None=Cookie(default=None)):user=current_user(job_session);return require_db().get_profile(user["id"])
@app.put("/api/profile")
def put_profile(payload:dict[str,Any],job_session:str|None=Cookie(default=None)):
    user=current_user(job_session);profile=dict(payload);profile["onboarding_complete"]=True;repo=require_db();repo.save_profile(user["id"],profile);return repo.get_profile(user["id"])

@app.get("/api/stats")
def stats():return dict(require_db().counts())
@app.get("/api/jobs")
def jobs(limit:int=50,min_score:int=0,source:str|None=None):return [dict(row) for row in require_db().top(max(1,min(limit,100)),source) if int(row.get("score") or 0)>=max(0,min_score)]
@app.get("/api/expiring")
def expiring(hours:int=72):return [dict(row) for row in require_db().expiring(max(1,min(hours,720)))]
@app.get("/api/applications")
def applications(limit:int=100,job_session:str|None=Cookie(default=None)):
    user=current_user(job_session);return [dict(row) for row in require_db().applications(user["id"],max(1,min(limit,100)))]
@app.patch("/api/applications/{application_id}")
def update_application(application_id:int,payload:dict[str,Any],job_session:str|None=Cookie(default=None)):
    current_user(job_session);status=payload.get("status")
    if not status:raise HTTPException(400,"status is required")
    try:require_db().update_application_status(application_id,status)
    except ValueError as exc:raise HTTPException(400,str(exc))
    return {"status":"updated","application_id":application_id,"new_status":status}
@app.get("/api/rag/status")
def rag_status(job_session:str|None=Cookie(default=None)):
    current_user(job_session)
    with require_db().conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS rag_documents (id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,chunks INTEGER DEFAULT 0,created_at TIMESTAMPTZ DEFAULT NOW())");count=c.execute("SELECT COALESCE(SUM(chunks),0) AS chunks,COUNT(*) AS documents FROM rag_documents").fetchone();c.commit()
    configured=bool(os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_MODEL"));return {"configured":configured,"documents":count["documents"],"chunks":count["chunks"],"message":f"{count['documents']} document(s) · {count['chunks']} chunk(s) indexed" if count["documents"] else "Knowledge base is ready for CV ingestion"}

@app.get("/api/portals")
def portals():
    counts={x["source"]:x for x in require_db().portal_counts()};return [{**p,"job_count":int(counts.get(p["name"],{}).get("jobs",0) or 0),"last_seen":counts.get(p["name"],{}).get("last_seen")} for p in portal_cards()]
@app.get("/api/portals/runs")
def portal_runs(job_session:str|None=Cookie(default=None)):
    current_user(job_session);return [dict(x) for x in require_db().portal_runs(100)]

PORTAL_COLLECTORS={"startup_jobs":collect_startup_jobs,"topstartups":collect_topstartups,"thehub":collect_thehub,"workinstartups":collect_workinstartups,"startupmap":collect_startupmap}
@app.post("/api/portals/{portal_key}/screen")
def screen_portal(portal_key:str,job_session:str|None=Cookie(default=None)):
    user=current_user(job_session);repo=require_db();portal=next((p for p in PORTALS if p.key==portal_key),None)
    if not portal:raise HTTPException(404,"Unknown portal")
    if portal.mode=="link":return {"status":"link_only","portal":portal.__dict__,"message":"Use the portal's native search/account experience; automated scraping is not enabled for this portal."}
    if portal_key in {"himalayas","greenhouse","lever","ashby"}:
        from job_agent.pipeline import run
        ranked=run(repo.get_profile(user["id"]),user["id"]);return {"status":"completed","portal":portal_key,"discovered":len(ranked),"message":"Portal is included in the full hunt."}
    collector=PORTAL_COLLECTORS.get(portal_key)
    if not collector:raise HTTPException(400,"Portal adapter is not configured")
    try:
        profile=repo.get_profile(user["id"]);raw=[normalize(j) for j in collector()]
        ranked=sorted(((score_with_profile(j,profile),j,explain_with_profile(j,profile)) for j in dedupe(raw)),key=lambda x:x[0],reverse=True);saved=0
        for s,j,reasons in ranked:
            job_id=repo.upsert(j,s,reasons);saved+=1
            if s>=85:repo.queue_application(job_id,"software-engineering",user["id"])
        repo.log_portal_run(portal.name,"completed",len(ranked),saved)
        return {"status":"completed","portal":portal.name,"discovered":len(ranked),"saved":saved,"jobs":[{"title":j.title,"company":j.company,"score":s,"url":j.url} for s,j,_ in ranked[:20]]}
    except Exception as exc:
        repo.log_portal_run(portal.name,"failed",0,0,type(exc).__name__);raise HTTPException(502,f"Portal screening failed: {type(exc).__name__}")

@app.post("/api/hunt")
def hunt(job_session:str|None=Cookie(default=None)):
    user=current_user(job_session)
    try:
        from job_agent.pipeline import run
        ranked=run(require_db().get_profile(user["id"]),user["id"]);return {"status":"completed","discovered":len(ranked),"strong_matches":sum(1 for x in ranked if x[0]>=85),"message":"All configured discovery sources were screened and jobs were saved to Neon"}
    except Exception as exc:raise HTTPException(500,f"Job hunt failed: {type(exc).__name__}: {exc}")
