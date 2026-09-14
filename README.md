# JOB-AUTOMATION

Production-oriented job discovery, matching, application-preparation and tracking system.

## Live web application

One Render Web Service serves the FastAPI backend and the web dashboard from the same origin.

The first visit shows **Login / Create account**. New users complete an onboarding profile with:

- Internship, full-time, or both
- Roles and skills
- City/country
- Remote preferences
- Preferred/excluded countries
- India work-eligibility preference
- Education and graduation information

The profile is stored per user in Neon PostgreSQL and drives screening/ranking.

## All Jobs

The **All Jobs** page now supports:

- All jobs
- Internship only
- Full-time only
- Part-time only
- Contract only
- Match-score filtering
- Portal/source filtering
- Keyword search across title, company, description and match reasons

Employment type is stored with each job and can be filtered without changing the saved jobs.

## CV / Resume storage

Every signed-in user can upload a CV from **Settings** or **RAG / Resume**.

Supported formats:

- PDF
- DOCX
- TXT
- MD

The original CV file is stored in Neon PostgreSQL in a per-user `cv_documents` record. The system also extracts text from supported PDF/DOCX/text files so the CV can feed the RAG/matching layer later. Maximum upload size is 10 MB.

Users can only access their own saved CV through the authenticated profile endpoint.

## Admin panel

Open `/admin` on the same Render service.

The admin panel is separate from normal user login and supports:

- Admin authentication
- View all registered users
- View user profile information
- View CV metadata and download a user's CV
- Edit a user's stored profile JSON
- Delete a user and their dependent profile, sessions, CV and applications

Configure these Render environment variables:

- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH` (recommended) or `ADMIN_PASSWORD`

`ADMIN_PASSWORD_HASH` uses the same scrypt password format as user accounts. Never commit an admin password or hash to GitHub. Use Render Environment Variables / Secret storage.

## Portal coverage

The dashboard has a **Job Portals** command center with separate cards and per-portal screening actions.

### Automated/public-source adapters

- Himalayas public JSON API
- Startup Jobs public RSS feeds
- Top Startups public jobs page
- The Hub public jobs page
- Work in Startups public site
- StartupMap public jobs pages
- Configurable Greenhouse public-board collector
- Configurable Lever public-postings collector
- Configurable Ashby public job-board collector
- Remotive public API
- Remote OK public API
- Jobicy public API
- Arbeitnow public API

### Native/link-only portals

- Wellfound — native portal/account flow is linked instead of using unauthorized automated scraping.
- Welcome to the Jungle — native profile/matching flow is linked instead of bypassing its account/matching experience.

The application never bypasses CAPTCHAs, authentication, anti-bot controls, or legal declarations.

## Job workflow

```text
User login
   -> onboarding profile
   -> optional CV upload -> Neon per-user CV record
   -> Run All Portals
   -> portal adapters
   -> normalize
   -> deduplicate
   -> eligibility + internship/full-time filtering
   -> profile-aware match score
   -> Neon PostgreSQL
   -> portal/source cards
   -> All Jobs filters
   -> job detail cards
   -> application review queue
   -> human approval
```

Opening a job card shows the portal source, score, matching reasons, job description and the original application link.

## Database

Neon/PostgreSQL stores jobs, users, secure session hashes, per-user profiles, CV documents, applications, portal screening runs and admin sessions.

Never commit `DATABASE_URL`, admin credentials, or any other secret to GitHub. Keep secrets in Render/GitHub secret storage.

## Automation

GitHub Actions runs the scheduled hunt. The web dashboard also provides a manual **Run All Portals** action for the signed-in user.

Required GitHub/Render secrets include:

- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Optional source configuration:

- `GREENHOUSE_BOARDS`
- `LEVER_SITES`
- `ASHBY_BOARDS`

## Safety

The system is approval-first. It can prepare resumes, cover letters, application answers and form data, but it must not bypass CAPTCHA, authentication, anti-bot controls or legal declarations, and it must not invent candidate information. Sensitive questions stop for human review.

## Run locally

```bash
pip install -r requirements.txt
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.
