# JOB-AUTOMATION

Production-oriented job discovery, matching, application-preparation and tracking system.

## Live web application

One Render Web Service now runs a **Next.js 16 frontend + FastAPI backend** together in Docker. The frontend is a futuristic career command center inspired by the supplied visual reference: dark glass cards, cyan/blue/purple gradients, orbital/globe visuals, AI assistant, job metrics, portal strip, goal progress and activity feed.

The frontend uses the modern Next.js App Router, React 19, Tailwind CSS v4, Motion, Lucide and shadcn-style open-code UI primitives. The visual effects are independently implemented for JOB-AUTOMATION rather than copying another site's proprietary CSS/source/assets.

The first visit shows **Login / Create account**. New users complete an onboarding profile with:

- Internship, full-time, or both
- Roles and skills
- City/country
- Remote preferences
- Preferred/excluded countries
- India work-eligibility preference
- Education and graduation information

The profile is stored per user in Neon PostgreSQL and drives screening/ranking.

## Frontend architecture

```text
frontend/
  app/
    page.tsx          # Dashboard, jobs, portals, applications, RAG, globe, analytics, settings
    layout.tsx
    globals.css       # Futuristic responsive design system
  components/ui/
    button.tsx
    card.tsx
  lib/utils.ts

Next.js 16.3.3
React 19.2
Tailwind CSS 4
Motion 12
Lucide React
shadcn/ui-compatible components.json
```

Next.js rewrites `/api/*` and `/health` to the private FastAPI process on `127.0.0.1:8000`, so authentication cookies, Neon data, CV upload and all existing API behavior stay on the same origin.

## Android app (Capacitor)

The project includes a Capacitor Android shell so the same responsive web application can be installed as an Android APK. The Android shell loads the production Render application over HTTPS, so login, Neon data, portal screening and the existing backend continue to work from the app.

### Build from GitHub Actions

Open **Actions → Android App → Run workflow**. The workflow:

1. Installs Node.js and Java.
2. Installs Capacitor.
3. Generates the Android project.
4. Syncs the Capacitor configuration.
5. Builds an installable debug APK.
6. Uploads `app-debug.apk` as a workflow artifact.

The workflow accepts a `server_url` input. Set it to the exact Render URL of the deployed JOB-AUTOMATION service if it differs from the default.

### Local Android build

```bash
npm install
npx cap add android
npx cap sync android
cd android
./gradlew assembleDebug
```

The mobile UI is responsive for phones and tablets, including the futuristic dashboard, global job explorer, job cards, portals, applications, RAG/resume and settings screens.

## All Jobs

The **Job Search** page supports:

- All jobs
- Internship only
- Full-time only
- Part-time only
- Contract only
- Match-score filtering
- Portal/source filtering
- Keyword search across title, company and location

Employment type is stored with each job and can be filtered without changing the saved jobs.

## CV / Resume storage

Every signed-in user can upload a CV from **AI Resume (RAG)** or **Settings**.

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
   -> Job Search filters
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

## Run locally — full stack

### Docker

```bash
docker build -t job-automation .
docker run --env-file .env -p 3000:3000 job-automation
```

Open `http://127.0.0.1:3000`.

### Frontend development

```bash
npm install
npm run dev:web
```

The Next.js development server runs on port 3000 and rewrites `/api/*` to a FastAPI server on port 8000. Start the backend separately:

```bash
pip install -r requirements.txt
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

