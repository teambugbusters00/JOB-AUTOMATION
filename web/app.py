import hashlib
import hmac
import io
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from job_agent.database.repository import JobRepository
from job_agent.portals import PORTALS, portal_cards, collect_startup_jobs, collect_topstartups, collect_thehub, collect_workinstartups, collect_startupmap
from job_agent.matcher import score_with_profile, explain_with_profile
from job_agent.models import dedupe, india_eligible, normalize
from .security import SESSION_COOKIE, hash_password, verify_password, new_session

BASE = Path(__file__).resolve().parent
app = FastAPI(title="JOB-AUTOMATION API", version="2.1.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

ADMIN_COOKIE = "job_admin_session"
ADMIN_SESSION_DAYS = 8
MAX_CV_BYTES = 10 * 1024 * 1024
ALLOWED_CV_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def db():
    return JobRepository(os.getenv("DATABASE_URL")) if os.getenv("DATABASE_URL") else None


def require_db():
    repo = db()
    if repo is None:
        raise HTTPException(503, "DATABASE_URL is not configured")
    repo.init()
    return repo


def cookie_secure():
    return os.getenv("ENVIRONMENT", "production").lower() == "production"


def current_user(session: str | None):
    if not session:
        raise HTTPException(401, "Login required")
    user = require_db().session_user(hashlib.sha256(session.encode()).hexdigest())
    if not user:
        raise HTTPException(401, "Session expired. Please log in again.")
    return user


def public_user(user):
    return {"id": user["id"], "email": user["email"], "created_at": user.get("created_at"), "last_login_at": user.get("last_login_at")}


def profile_response(repo, user_id):
    profile = dict(repo.get_profile(user_id) or {})
    cv = repo.get_cv_meta(user_id)
    profile["cv"] = dict(cv) if cv else None
    return profile


def create_cookie(response: Response, name: str, token: str, days: int):
    response.set_cookie(name, token, max_age=days * 24 * 3600, httponly=True, samesite="lax", secure=cookie_secure(), path="/")


def admin_credentials_configured():
    return bool(os.getenv("ADMIN_EMAIL") and (os.getenv("ADMIN_PASSWORD_HASH") or os.getenv("ADMIN_PASSWORD")))


def verify_admin_password(password: str):
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if stored_hash:
        return verify_password(password, stored_hash)
    stored = os.getenv("ADMIN_PASSWORD", "")
    return bool(stored) and hmac.compare_digest(password, stored)


def current_admin(session: str | None):
    if not session:
        raise HTTPException(401, "Admin login required")
    admin = require_db().admin_session(hashlib.sha256(session.encode()).hexdigest())
    if not admin:
        raise HTTPException(401, "Admin session expired. Please log in again.")
    return admin


def extract_cv_text(filename: str, content_type: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext in {".txt", ".md"} or content_type.startswith("text/"):
        return data.decode("utf-8", errors="ignore")[:200_000]
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            return "\n".join((page.extract_text() or "") for page in reader.pages)[:200_000]
        except Exception:
            return ""
    if ext == ".docx":
        try:
            from docx import Document
            document = Document(io.BytesIO(data))
            return "\n".join(p.text for p in document.paragraphs)[:200_000]
        except Exception:
            return ""
    return ""


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(BASE / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_root():
    return FileResponse(BASE / "admin.html")


@app.get("/api")
def api_info() -> dict[str, Any]:
    return {"name": "JOB-AUTOMATION API", "status": "ok", "version": "2.1.0", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/health")
def health():
    repo = db()
    if repo is None:
        return {"status": "ok", "database": "not_configured"}
    try:
        repo.init()
        return {"status": "ok", "database": "connected", "counts": dict(repo.counts()), "admin_configured": admin_credentials_configured()}
    except Exception as exc:
        return {"status": "degraded", "database": "error", "error": type(exc).__name__}


@app.post("/api/auth/register")
def register(payload: dict[str, Any], response: Response):
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if "@" not in email:
        raise HTTPException(400, "Enter a valid email")
    try:
        ph = hash_password(password)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    repo = require_db()
    try:
        user = repo.create_user(email, ph)
    except Exception as exc:
        raise HTTPException(409, "An account with that email already exists") from exc
    token, token_hash, expires = new_session()
    repo.create_session(user["id"], token_hash, expires)
    create_cookie(response, SESSION_COOKIE, token, 14)
    return {"user": public_user(user), "profile": profile_response(repo, user["id"])}


@app.post("/api/auth/login")
def login(payload: dict[str, Any], response: Response):
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not email or not password:
        raise HTTPException(400, "Email and password are required")
    repo = require_db()
    user = repo.get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password. If you do not have an account, use Create an account.")
    repo.set_login(user["id"])
    token, token_hash, expires = new_session()
    repo.create_session(user["id"], token_hash, expires)
    create_cookie(response, SESSION_COOKIE, token, 14)
    user = repo.get_user(user["id"])
    return {"user": public_user(user), "profile": profile_response(repo, user["id"])}


@app.post("/api/auth/logout")
def logout(response: Response, job_session: str | None = Cookie(default=None)):
    if job_session:
        require_db().delete_session(hashlib.sha256(job_session.encode()).hexdigest())
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"status": "logged_out"}


@app.get("/api/auth/me")
def me(job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    repo = require_db()
    return {"user": public_user(user), "profile": profile_response(repo, user["id"])}


@app.get("/api/profile")
def get_profile(job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    return profile_response(require_db(), user["id"])


@app.put("/api/profile")
def put_profile(payload: dict[str, Any], job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    profile = dict(payload)
    profile.pop("cv", None)
    profile["onboarding_complete"] = True
    repo = require_db()
    repo.save_profile(user["id"], profile)
    return profile_response(repo, user["id"])


@app.post("/api/profile/cv")
async def upload_cv(file: UploadFile = File(...), job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    filename = Path(file.filename or "cv").name
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_CV_EXTENSIONS:
        raise HTTPException(400, "CV must be PDF, DOCX, TXT or MD")
    data = await file.read(MAX_CV_BYTES + 1)
    if len(data) > MAX_CV_BYTES:
        raise HTTPException(413, "CV is too large. Maximum size is 10 MB")
    content_type = file.content_type or "application/octet-stream"
    text = extract_cv_text(filename, content_type, data)
    repo = require_db()
    saved = repo.save_cv(user["id"], filename, content_type, data, text)
    profile = repo.get_profile(user["id"])
    profile["cv_uploaded"] = True
    repo.save_profile(user["id"], profile)
    return {"status": "saved", "cv": dict(saved), "extracted_characters": len(text)}


@app.get("/api/profile/cv")
def download_cv(job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    cv = require_db().get_cv(user["id"])
    if not cv:
        raise HTTPException(404, "No CV uploaded")
    return StreamingResponse(io.BytesIO(bytes(cv["file_data"])), media_type=cv["content_type"], headers={"Content-Disposition": f'inline; filename="{cv["filename"].replace(chr(34), "")}"'})


@app.get("/api/stats")
def stats():
    return dict(require_db().counts())


@app.get("/api/jobs")
def jobs(limit: int = 100, min_score: int = 0, source: str | None = None, employment_type: str = "all"):
    allowed = {"all", "internship", "full-time", "part-time", "contract"}
    employment_type = employment_type.lower().strip()
    if employment_type not in allowed:
        raise HTTPException(400, "Unsupported employment type")
    rows = require_db().top(max(1, min(limit, 200)), source, employment_type)
    return [dict(row) for row in rows if int(row.get("score") or 0) >= max(0, min_score)]


@app.get("/api/expiring")
def expiring(hours: int = 72):
    return [dict(row) for row in require_db().expiring(max(1, min(hours, 720)))]


@app.get("/api/applications")
def applications(limit: int = 100, job_session: str | None = Cookie(default=None)):
    return [dict(row) for row in require_db().applications(current_user(job_session)["id"], max(1, min(limit, 100)))]


@app.patch("/api/applications/{application_id}")
def update_application(application_id: int, payload: dict[str, Any], job_session: str | None = Cookie(default=None)):
    current_user(job_session)
    status = payload.get("status")
    if not status:
        raise HTTPException(400, "status is required")
    try:
        require_db().update_application_status(application_id, status)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"status": "updated", "application_id": application_id, "new_status": status}


@app.get("/api/rag/status")
def rag_status(job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    repo = require_db()
    cv = repo.get_cv_meta(user["id"])
    with repo.conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS rag_documents (id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,chunks INTEGER DEFAULT 0,created_at TIMESTAMPTZ DEFAULT NOW())")
        count = c.execute("SELECT COALESCE(SUM(chunks),0) AS chunks,COUNT(*) AS documents FROM rag_documents").fetchone()
        c.commit()
    configured = bool(os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_MODEL"))
    return {"configured": configured, "documents": count["documents"], "chunks": count["chunks"], "cv_uploaded": bool(cv), "cv_filename": cv["filename"] if cv else None, "message": f"CV {cv['filename']} saved · {count['documents']} document(s) · {count['chunks']} chunk(s) indexed" if cv else "Upload your CV to store it securely per user in Neon"}


@app.get("/api/portals")
def portals():
    repo = require_db()
    counts = {str(x["source"]).strip().lower(): x for x in repo.portal_counts()}
    aliases = {"himalayas": ["himalayas"], "greenhouse": ["greenhouse"], "lever": ["lever"], "ashby": ["ashby"], "startup_jobs": ["startup jobs"], "topstartups": ["top startups"], "thehub": ["the hub"], "workinstartups": ["work in startups"], "startupmap": ["startupmap"]}
    cards = []
    for p in portal_cards():
        keys = aliases.get(p["key"], [p["name"].lower()])
        hits = [counts[k] for k in keys if k in counts]
        cards.append({**p, "job_count": sum(int(x["jobs"] or 0) for x in hits), "last_seen": max((x["last_seen"] for x in hits if x["last_seen"]), default=None)})
    return cards


@app.get("/api/portals/runs")
def portal_runs(job_session: str | None = Cookie(default=None)):
    current_user(job_session)
    return [dict(x) for x in require_db().portal_runs(100)]


PORTAL_COLLECTORS = {"startup_jobs": collect_startup_jobs, "topstartups": collect_topstartups, "thehub": collect_thehub, "workinstartups": collect_workinstartups, "startupmap": collect_startupmap}


@app.post("/api/portals/{portal_key}/screen")
def screen_portal(portal_key: str, job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    repo = require_db()
    portal = next((p for p in PORTALS if p.key == portal_key), None)
    if not portal:
        raise HTTPException(404, "Unknown portal")
    if portal.mode == "link":
        return {"status": "link_only", "portal": portal.__dict__, "message": "Use the portal's native search/account experience; automated scraping is not enabled for this portal."}
    if portal_key in {"himalayas", "greenhouse", "lever", "ashby"}:
        from job_agent.pipeline import run
        ranked = run(repo.get_profile(user["id"]), user["id"])
        return {"status": "completed", "portal": portal_key, "discovered": len(ranked), "message": "Portal is included in the full hunt."}
    collector = PORTAL_COLLECTORS.get(portal_key)
    if not collector:
        raise HTTPException(400, "Portal adapter is not configured")
    try:
        profile = repo.get_profile(user["id"])
        raw = [normalize(j) for j in collector()]
        ranked = sorted(((score_with_profile(j, profile), j, explain_with_profile(j, profile)) for j in dedupe(raw)), key=lambda x: x[0], reverse=True)
        saved = 0
        for s, j, reasons in ranked:
            job_id = repo.upsert(j, s, reasons)
            saved += 1
            if s >= 85:
                repo.queue_application(job_id, "software-engineering", user["id"])
        repo.log_portal_run(portal.name, "completed", len(ranked), saved)
        return {"status": "completed", "portal": portal.name, "discovered": len(ranked), "saved": saved, "jobs": [{"title": j.title, "company": j.company, "score": s, "url": j.url} for s, j, _ in ranked[:20]]}
    except Exception as exc:
        try:
            repo.log_portal_run(portal.name, "failed", 0, 0, type(exc).__name__)
        except Exception:
            pass
        raise HTTPException(502, f"Portal screening failed: {type(exc).__name__}")


@app.post("/api/hunt")
def hunt(job_session: str | None = Cookie(default=None)):
    user = current_user(job_session)
    try:
        from job_agent.pipeline import run
        ranked = run(require_db().get_profile(user["id"]), user["id"])
        return {"status": "completed", "discovered": len(ranked), "strong_matches": sum(1 for x in ranked if x[0] >= 85), "message": "All configured discovery sources were screened and jobs were saved to Neon"}
    except Exception as exc:
        raise HTTPException(500, f"Job hunt failed: {type(exc).__name__}: {exc}")


# -------------------- Admin --------------------

@app.post("/api/admin/login")
def admin_login(payload: dict[str, Any], response: Response):
    if not admin_credentials_configured():
        raise HTTPException(503, "Admin login is not configured. Set ADMIN_EMAIL and ADMIN_PASSWORD_HASH (or ADMIN_PASSWORD) in Render environment variables.")
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    configured_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    if email != configured_email or not verify_admin_password(password):
        raise HTTPException(401, "Invalid admin email or password")
    token, token_hash, expires = new_session()
    repo = require_db()
    repo.create_admin_session(email, token_hash, datetime.now(timezone.utc) + timedelta(days=ADMIN_SESSION_DAYS))
    create_cookie(response, ADMIN_COOKIE, token, ADMIN_SESSION_DAYS)
    return {"email": email, "status": "authenticated"}


@app.post("/api/admin/logout")
def admin_logout(response: Response, job_admin_session: str | None = Cookie(default=None)):
    if job_admin_session:
        require_db().delete_admin_session(hashlib.sha256(job_admin_session.encode()).hexdigest())
    response.delete_cookie(ADMIN_COOKIE, path="/")
    return {"status": "logged_out"}


@app.get("/api/admin/me")
def admin_me(job_admin_session: str | None = Cookie(default=None)):
    admin = current_admin(job_admin_session)
    return {"email": admin["admin_email"], "status": "authenticated"}


@app.get("/api/admin/users")
def admin_users(job_admin_session: str | None = Cookie(default=None)):
    current_admin(job_admin_session)
    rows = require_db().list_users()
    out = []
    for row in rows:
        item = dict(row)
        item["profile"] = item.get("profile") or {}
        item["cv"] = {"filename": item.pop("cv_filename", None), "content_type": item.pop("cv_content_type", None), "file_size": item.pop("cv_file_size", None), "uploaded_at": item.pop("cv_uploaded_at", None)}
        out.append(item)
    return out


@app.get("/api/admin/users/{user_id}/cv")
def admin_download_cv(user_id: int, job_admin_session: str | None = Cookie(default=None)):
    current_admin(job_admin_session)
    cv = require_db().get_cv(user_id)
    if not cv:
        raise HTTPException(404, "User has no CV")
    filename = cv["filename"].replace('"', "")
    return StreamingResponse(io.BytesIO(bytes(cv["file_data"])), media_type=cv["content_type"], headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.put("/api/admin/users/{user_id}/profile")
def admin_update_profile(user_id: int, payload: dict[str, Any], job_admin_session: str | None = Cookie(default=None)):
    current_admin(job_admin_session)
    profile = dict(payload)
    profile.pop("cv", None)
    return {"user_id": user_id, "profile": require_db().admin_update_profile(user_id, profile)}


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: int, job_admin_session: str | None = Cookie(default=None)):
    current_admin(job_admin_session)
    deleted = require_db().delete_user(user_id)
    if not deleted:
        raise HTTPException(404, "User not found")
    return {"status": "deleted", "user": dict(deleted)}
