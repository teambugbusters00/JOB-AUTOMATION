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
 score INTEGER DEFAULT 0,
 match_reasons JSONB DEFAULT '[]'::jsonb,
 status TEXT DEFAULT 'DISCOVERED',
 first_seen_at TIMESTAMPTZ DEFAULT NOW(),
 last_seen_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
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
            c.execute("""
                INSERT INTO jobs (fingerprint, external_id, source, title, company, location, remote,
                    employment_type, salary, description, url, score, match_reasons, last_seen_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (fingerprint) DO UPDATE SET
                    score=EXCLUDED.score, match_reasons=EXCLUDED.match_reasons,
                    url=EXCLUDED.url, description=EXCLUDED.description, last_seen_at=NOW()
                RETURNING id
            """, (job.fingerprint, job.external_id, job.source, job.title, job.company, job.location,
                  job.remote, job.employment_type, job.salary, job.description, job.url, score, Jsonb(reasons)))
            row = c.fetchone()
            c.commit()
            return row["id"]

    def top(self, limit=20):
        with self.conn() as c:
            return c.execute("SELECT * FROM jobs WHERE score >= 75 ORDER BY score DESC, last_seen_at DESC LIMIT %s", (limit,)).fetchall()

    def counts(self):
        with self.conn() as c:
            return c.execute("SELECT COUNT(*) total, COUNT(*) FILTER (WHERE score >= 85) strong, COUNT(*) FILTER (WHERE status IN ('READY_FOR_REVIEW','APPROVED')) queue FROM jobs").fetchone()
