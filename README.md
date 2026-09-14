# JOB-AUTOMATION

Production-oriented job discovery, matching, application-preparation and tracking system for Vijay Ramdev.

## What is live in this repository

- Daily GitHub Actions job hunt at 08:00 IST
- Manual workflow trigger
- Himalayas public JSON API collector
- Configurable Greenhouse public-board collector
- Configurable Lever public-postings collector
- Configurable Ashby public job-board collector
- Normalization and deterministic job fingerprints
- India/worldwide eligibility filtering
- Role + skill + student/entry-level matching
- PostgreSQL persistence with upserts and indexes
- Telegram daily report
- Daily report artifact retained for 30 days
- CI tests on pushes and pull requests
- Application profile template
- Human-approval safety policy for application execution

## Production architecture

```text
Sources
  -> Collectors
  -> Normalize
  -> Deduplicate
  -> India eligibility
  -> Match + score
  -> PostgreSQL
  -> Daily report
  -> Telegram
  -> Application review queue
  -> Human approval
  -> Permitted browser/form automation
  -> Application tracking
```

## Important application policy

The system is approval-first. It can prepare resumes, cover letters, application answers and form data, but it must not bypass CAPTCHA, authentication, anti-bot controls, or legal declarations, and it must not invent candidate information. Sensitive questions stop for human review.

## GitHub Actions configuration

Required **Repository Secrets**:

- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Optional **Repository Variables**:

- `GREENHOUSE_BOARDS` — comma-separated public Greenhouse board slugs
- `LEVER_SITES` — comma-separated Lever site slugs
- `ASHBY_BOARDS` — comma-separated Ashby public job-board slugs

The default daily workflow already searches the user's target role families through Himalayas.

## Local run

```bash
pip install -r requirements.txt
python -m job_agent
pytest -q
```

For PostgreSQL persistence locally:

```bash
set DATABASE_URL=postgresql://...
python -m job_agent
```

## Next production layer

The discovery and tracking foundation is now implemented. The next layer is the application workspace: resume variants, tailored cover letters, structured application answers, approval UI, application event history, permitted Playwright form filling, deadline monitoring, and a dashboard/API.

## Data-source note

Himalayas is used through its public JSON API. When its data is displayed in a UI, retain source attribution and a link back to Himalayas as required by its API documentation.
