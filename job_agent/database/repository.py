import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from ..models import Job

DDL = '''
CREATE TABLE IF NOT EXISTS jobs (
 id BIGSERIAL PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL, external_id TEXT, source TEXT NOT NULL,
 title TEXT NOT NULL, company TEXT NOT NULL, location TEXT, remote TEXT, employment_type TEXT,
 salary TEXT, description TEXT, url TEXT NOT NULL, deadline TIMESTAMPTZ, score INTEGER DEFAULT 0,
 match_reasons JSONB DEFAULT '[]'::jsonb, status TEXT DEFAULT 'DISCOVERED',
 first_seen_at TIMESTAMPTZ DEFAULT NOW(), last_seen_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS deadline TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_deadline ON jobs(deadline);
CREATE TABLE IF NOT EXISTS users (
 id BIGSERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 created_at TIMESTAMPTZ DEFAULT NOW(), last_login_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS user_profiles (
 user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, profile JSONB NOT NULL DEFAULT '{}'::jsonb,
 updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS sessions (
 id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 token_hash TEXT UNIQUE NOT NULL, expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
CREATE TABLE IF NOT EXISTS applications (
 id BIGSERIAL PRIMARY KEY, job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
 user_id BIGINT REFERENCES users(id) ON DELETE CASCADE, status TEXT NOT NULL DEFAULT 'READY_FOR_REVIEW',
 resume_variant TEXT, cover_letter TEXT, prepared_answers JSONB DEFAULT '{}'::jsonb,
 submitted_at TIMESTAMPTZ, updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE applications DROP CONSTRAINT IF EXISTS applications_job_id_key;
CREATE UNIQUE INDEX IF NOT EXISTS idx_applications_user_job ON applications(user_id, job_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE TABLE IF NOT EXISTS portal_runs (
 id BIGSERIAL PRIMARY KEY, portal TEXT NOT NULL, status TEXT NOT NULL, discovered INTEGER DEFAULT 0,
 saved INTEGER DEFAULT 0, error TEXT, ran_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_portal_runs_portal ON portal_runs(portal, ran_at DESC);
CREATE TABLE IF NOT EXISTS cv_documents (
 id BIGSERIAL PRIMARY KEY,
 user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 filename TEXT NOT NULL,
 content_type TEXT NOT NULL,
 file_size BIGINT NOT NULL,
 file_data BYTEA NOT NULL,
 extracted_text TEXT DEFAULT '',
 uploaded_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cv_documents_user ON cv_documents(user_id);
CREATE TABLE IF NOT EXISTS admin_sessions (
 id BIGSERIAL PRIMARY KEY,
 admin_email TEXT NOT NULL,
 token_hash TEXT UNIQUE NOT NULL,
 expires_at TIMESTAMPTZ NOT NULL,
 created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expiry ON admin_sessions(expires_at);
'''

class JobRepository:
    def __init__(self,url=None):
        self.url=url or os.environ.get("DATABASE_URL")
        if not self.url: raise RuntimeError("DATABASE_URL is required for production persistence")
    @contextmanager
    def conn(self):
        with psycopg.connect(self.url,row_factory=dict_row) as c: yield c
    def init(self):
        with self.conn() as c: c.execute(DDL); c.commit()
    def upsert(self,job:Job,score:int,reasons:list[str]):
        with self.conn() as c:
            row=c.execute("""INSERT INTO jobs(fingerprint,external_id,source,title,company,location,remote,employment_type,salary,description,url,deadline,score,match_reasons,last_seen_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT(fingerprint) DO UPDATE SET score=EXCLUDED.score,match_reasons=EXCLUDED.match_reasons,url=EXCLUDED.url,description=EXCLUDED.description,deadline=EXCLUDED.deadline,source=EXCLUDED.source,last_seen_at=NOW() RETURNING id""",
            (job.fingerprint,job.external_id,job.source,job.title,job.company,job.location,job.remote,job.employment_type,job.salary,job.description,job.url,job.deadline,score,Jsonb(reasons))).fetchone(); c.commit(); return row["id"]
    def queue_application(self,job_id:int,resume_variant:str,user_id=None):
        with self.conn() as c:
            if user_id: c.execute("INSERT INTO applications(job_id,user_id,status,resume_variant) VALUES(%s,%s,'READY_FOR_REVIEW',%s) ON CONFLICT(user_id,job_id) WHERE user_id IS NOT NULL DO NOTHING",(job_id,user_id,resume_variant))
            else: c.execute("INSERT INTO applications(job_id,status,resume_variant) VALUES(%s,'READY_FOR_REVIEW',%s) ON CONFLICT DO NOTHING",(job_id,resume_variant))
            c.commit()
    def update_application_status(self,application_id:int,status:str):
        allowed={"READY_FOR_REVIEW","APPROVED","PREPARING","READY_TO_SUBMIT","SUBMITTED","ASSESSMENT","INTERVIEW","OFFER","REJECTED","WITHDRAWN"}
        if status not in allowed: raise ValueError(f"Unsupported application status: {status}")
        with self.conn() as c: c.execute("UPDATE applications SET status=%s,updated_at=NOW() WHERE id=%s",(status,application_id)); c.commit()
    def expiring(self,hours=72):
        with self.conn() as c: return c.execute("SELECT title,company,url,score,deadline FROM jobs WHERE deadline IS NOT NULL AND deadline>NOW() AND deadline<=NOW()+(%s*INTERVAL '1 hour') ORDER BY deadline ASC",(hours,)).fetchall()
    def top(self,limit=20,source=None,employment_type=None):
        with self.conn() as c:
            clauses=[]; params=[]
            if source: clauses.append("source=%s"); params.append(source)
            if employment_type and employment_type != "all": clauses.append("lower(replace(employment_type,' ', '-'))=%s"); params.append(employment_type.lower().replace(' ','-'))
            where=(" WHERE " + " AND ".join(clauses)) if clauses else ""
            params.append(limit)
            return c.execute(f"SELECT * FROM jobs{where} ORDER BY score DESC,last_seen_at DESC LIMIT %s",tuple(params)).fetchall()
    def counts(self):
        with self.conn() as c: return c.execute("SELECT (SELECT COUNT(*) FROM jobs) AS total,(SELECT COUNT(*) FROM jobs WHERE score>=85) AS strong,(SELECT COUNT(*) FROM applications WHERE status IN ('READY_FOR_REVIEW','APPROVED','READY_TO_SUBMIT')) AS queue").fetchone()
    def portal_counts(self):
        with self.conn() as c: return c.execute("SELECT source,COUNT(*) AS jobs,MAX(last_seen_at) AS last_seen FROM jobs GROUP BY source ORDER BY jobs DESC").fetchall()
    def get_user_by_email(self,email):
        with self.conn() as c: return c.execute("SELECT * FROM users WHERE lower(email)=lower(%s)",(email,)).fetchone()
    def get_user(self,user_id):
        with self.conn() as c: return c.execute("SELECT id,email,created_at,last_login_at FROM users WHERE id=%s",(user_id,)).fetchone()
    def create_user(self,email,password_hash):
        with self.conn() as c: row=c.execute("INSERT INTO users(email,password_hash) VALUES(lower(%s),%s) RETURNING id,email,created_at",(email,password_hash)).fetchone(); c.commit(); return row
    def set_login(self,user_id):
        with self.conn() as c: c.execute("UPDATE users SET last_login_at=NOW() WHERE id=%s",(user_id,)); c.commit()
    def create_session(self,user_id,token_hash,expires_at):
        with self.conn() as c: c.execute("INSERT INTO sessions(user_id,token_hash,expires_at) VALUES(%s,%s,%s)",(user_id,token_hash,expires_at)); c.commit()
    def session_user(self,token_hash):
        with self.conn() as c: return c.execute("SELECT u.id,u.email,u.created_at,u.last_login_at,s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s AND s.expires_at>NOW()",(token_hash,)).fetchone()
    def delete_session(self,token_hash):
        with self.conn() as c: c.execute("DELETE FROM sessions WHERE token_hash=%s",(token_hash,)); c.commit()
    def get_profile(self,user_id):
        with self.conn() as c:
            row=c.execute("SELECT profile FROM user_profiles WHERE user_id=%s",(user_id,)).fetchone(); return row["profile"] if row else {}
    def save_profile(self,user_id,profile):
        with self.conn() as c: c.execute("INSERT INTO user_profiles(user_id,profile) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET profile=EXCLUDED.profile,updated_at=NOW()",(user_id,Jsonb(profile))); c.commit()
    def applications(self,user_id=None,limit=100):
        with self.conn() as c:
            if user_id: return c.execute("SELECT a.id,a.status,a.resume_variant,a.updated_at,j.id AS job_id,j.title,j.company,j.url,j.score,j.source FROM applications a JOIN jobs j ON j.id=a.job_id WHERE a.user_id=%s ORDER BY a.updated_at DESC LIMIT %s",(user_id,limit)).fetchall()
            return c.execute("SELECT a.id,a.status,a.resume_variant,a.updated_at,j.id AS job_id,j.title,j.company,j.url,j.score,j.source FROM applications a JOIN jobs j ON j.id=a.job_id ORDER BY a.updated_at DESC LIMIT %s",(limit,)).fetchall()
    def log_portal_run(self,portal,status,discovered=0,saved=0,error=None):
        with self.conn() as c: c.execute("INSERT INTO portal_runs(portal,status,discovered,saved,error) VALUES(%s,%s,%s,%s,%s)",(portal,status,discovered,saved,error)); c.commit()
    def portal_runs(self,limit=100):
        with self.conn() as c: return c.execute("SELECT * FROM portal_runs ORDER BY ran_at DESC LIMIT %s",(limit,)).fetchall()
    def save_cv(self,user_id,filename,content_type,file_data,extracted_text):
        with self.conn() as c:
            row=c.execute("""INSERT INTO cv_documents(user_id,filename,content_type,file_size,file_data,extracted_text)
            VALUES(%s,%s,%s,%s,%s,%s)
            ON CONFLICT(user_id) DO UPDATE SET filename=EXCLUDED.filename,content_type=EXCLUDED.content_type,file_size=EXCLUDED.file_size,file_data=EXCLUDED.file_data,extracted_text=EXCLUDED.extracted_text,uploaded_at=NOW()
            RETURNING id,filename,content_type,file_size,uploaded_at""",(user_id,filename,content_type,len(file_data),file_data,extracted_text)).fetchone(); c.commit(); return row
    def get_cv_meta(self,user_id):
        with self.conn() as c: return c.execute("SELECT id,filename,content_type,file_size,uploaded_at,length(extracted_text) AS text_length FROM cv_documents WHERE user_id=%s",(user_id,)).fetchone()
    def get_cv(self,user_id):
        with self.conn() as c: return c.execute("SELECT filename,content_type,file_size,file_data,extracted_text,uploaded_at FROM cv_documents WHERE user_id=%s",(user_id,)).fetchone()
    def list_users(self):
        with self.conn() as c:
            return c.execute("""SELECT u.id,u.email,u.created_at,u.last_login_at,p.profile,
                cv.filename AS cv_filename,cv.content_type AS cv_content_type,cv.file_size AS cv_file_size,cv.uploaded_at AS cv_uploaded_at
                FROM users u LEFT JOIN user_profiles p ON p.user_id=u.id LEFT JOIN cv_documents cv ON cv.user_id=u.id ORDER BY u.created_at DESC""").fetchall()
    def admin_update_profile(self,user_id,profile):
        if not self.get_user(user_id): raise ValueError("User not found")
        self.save_profile(user_id,profile); return self.get_profile(user_id)
    def update_user_password(self,user_id,password_hash):
        with self.conn() as c: c.execute("UPDATE users SET password_hash=%s WHERE id=%s",(password_hash,user_id)); c.commit()
    def delete_user(self,user_id):
        with self.conn() as c:
            row=c.execute("DELETE FROM users WHERE id=%s RETURNING id,email",(user_id,)).fetchone(); c.commit(); return row
    def create_admin_session(self,email,token_hash,expires_at):
        with self.conn() as c: c.execute("INSERT INTO admin_sessions(admin_email,token_hash,expires_at) VALUES(%s,%s,%s)",(email,token_hash,expires_at)); c.commit()
    def admin_session(self,token_hash):
        with self.conn() as c: return c.execute("SELECT admin_email,expires_at FROM admin_sessions WHERE token_hash=%s AND expires_at>NOW()",(token_hash,)).fetchone()
    def delete_admin_session(self,token_hash):
        with self.conn() as c: c.execute("DELETE FROM admin_sessions WHERE token_hash=%s",(token_hash,)); c.commit()
