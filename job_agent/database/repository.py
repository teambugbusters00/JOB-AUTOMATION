import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from ..models import Job

DDL = '''
CREATE TABLE IF NOT EXISTS jobs (
 id BIGSERIAL PRIMARY KEY,
 fingerprint TEXT UNIQUE NOT NULL,
 external_id TEXT,
 source TEXT NOT NULL,
 title TEXT NOT NULL,
 company TEXT NOT NULL,
 location TEXT,
 remote TEXT,
 employment_type TEXT,
 salary TEXT,
 description TEXT,
 url TEXT NOT NULL,
 deadline TIMESTAMPTZ,
 score INTEGER DEFAULT 0,
 match_reasons JSONB DEFAULT '[]'::jsonb,
 status TEXT DEFAULT 'DISCOVERED',
 first_seen_at TIMESTAMPTZ DEFAULT NOW(),
 last_seen_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS deadline TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_deadline ON jobs(deadline);

CREATE TABLE IF NOT EXISTS applications (
 id BIGSERIAL PRIMARY KEY,
 job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
 status TEXT NOT NULL DEFAULT 'READY_FOR_REVIEW',
 resume_variant TEXT,
 cover_letter TEXT,
 prepared_answers JSONB DEFAULT '{}'::jsonb,
 submitted_at TIMESTAMPTZ,
 updated_at TIMESTAMPTZ DEFAULT NOW(),
 UNIQUE(job_id)
);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
'''

class JobRepository:
    def __init__(self, url=None):
        self.url = url or os.environ.get("DATABASE_URL")
        if not self.url:
            raise RuntimeError("DATABASE_URL is required for production persistence")

    @contextmanager
    def conn(self):
        with psycopg.connect(self.url, row_factory=dict_row) as c:
            yield c

    def init(self):
        with self.conn() as c:
            c.execute(DDL)
            c.commit()

    def upsert(self, job: Job, score: int, reasons: list[str]):
        with self.conn() as c:
            row = c.execute("""
                INSERT INTO jobs (fingerprint, external_id, source, title, company, location, remote,
                    employment_type, salary, description, url, deadline, score, match_reasons, last_seen_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (fingerprint) DO UPDATE SET
                    score=EXCLUDED.score, match_reasons=EXCLUDED.match_reasons,
                    url=EXCLUDED.url, description=EXCLUDED.description, deadline=EXCLUDED.deadline, last_seen_at=NOW()
                RETURNING id
            """, (job.fingerprint, job.external_id, job.source, job.title, job.company, job.location,
                  job.remote, job.employment_type, job.salary, job.description, job.url, job.deadline, score, Jsonb(reasons))).fetchone()
            c.commit()
            return row["id"]

    def queue_application(self, job_id: int, resume_variant: str):
        with self.conn() as c:
            c.execute("""
                INSERT INTO applications(job_id, status, resume_variant)
                VALUES (%s, 'READY_FOR_REVIEW', %s)
                ON CONFLICT(job_id) DO NOTHING
            """, (job_id, resume_variant))
            c.commit()

    def update_application_status(self, application_id: int, status: str):
        allowed = {"READY_FOR_REVIEW", "APPROVED", "PREPARING", "READY_TO_SUBMIT", "SUBMITTED", "ASSESSMENT", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"}
        if status not in allowed:
            raise ValueError(f"Unsupported application status: {status}")
        with self.conn() as c:
            c.execute("UPDATE applications SET status=%s, updated_at=NOW() WHERE id=%s", (status, application_id))
            c.commit()

    def expiring(self, hours=72):
        with self.conn() as c:
            return c.execute("""
                SELECT title, company, url, score, deadline FROM jobs
                WHERE deadline IS NOT NULL AND deadline > NOW() AND deadline <= NOW() + (%s * INTERVAL '1 hour')
                ORDER BY deadline ASC
            """, (hours,)).fetchall()

    def top(self, limit=20, min_score=0):
        with self.conn() as c:
            return c.execute("""
                SELECT * FROM jobs
                WHERE score >= %s
                ORDER BY score DESC, last_seen_at DESC
                LIMIT %s
            """, (max(0, min_score), limit)).fetchall()

    def applications(self, limit=100):
        with self.conn() as c:
            return c.execute("""
                SELECT a.*, j.title, j.company, j.url, j.score, j.location, j.source
                FROM applications a JOIN jobs j ON j.id=a.job_id
                ORDER BY a.updated_at DESC LIMIT %s
            """, (limit,)).fetchall()

    def counts(self):
        with self.conn() as c:
            return c.execute("""
                SELECT
                  (SELECT COUNT(*) FROM jobs) AS total,
                  (SELECT COUNT(*) FROM jobs WHERE score >= 85) AS strong,
                  (SELECT COUNT(*) FROM applications WHERE status IN ('READY_FOR_REVIEW','APPROVED','READY_TO_SUBMIT')) AS queue
            """).fetchone()
