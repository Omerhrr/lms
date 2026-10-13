# Infohive LMS

A full-featured, industry-standard Learning Management System built as a **modular monolith**: a Nuxt 3 frontend, a FastAPI backend, and SQLAlchemy 2.0 ORM over a portable schema (SQLite by default, PostgreSQL-ready).

## Features

### Students
- Course catalog with categories, search and filtering
- Course preview pages and secure enrollment
- Learning experience with video lessons, rich text content and progress tracking
- Watch-only video player for pasted YouTube / Vimeo / .mp4 links: plays inside Infohive with its own controls, a click-shield over the embed (no "Watch on YouTube", logo or suggested-video links) and downloads disabled for files
- Drip release (lessons unlock N days after enrolling) and course prerequisites
- Private notes and bookmarks inside every lesson, plus a calendar of assignment due dates and lesson unlocks
- Downloadable PDF certificates
- **Live classes**: instructors schedule sessions per course (built-in Jitsi video room or a Zoom/Meet/Teams link); students are notified, see them on their dashboard and calendar, join from 15 minutes early, and attendance is recorded; recordings play in the watch-only player
- **Company website**: Home, About, Services, LMS/Courses, Contact (enquiries saved, emailed to the team, and listed under Admin → Enquiries), Privacy and Terms (drafts)
- Quizzes with auto-grading, multiple attempts and instant feedback
- Grades and certificates with public verification pages
- Course announcements and threaded discussions

### Instructors
- Course builder with a rich text editor (headings, lists, links, images, code) for lessons and course descriptions
- Student management and gradebook
- Announcements and per-course analytics
- Instructor dashboard with engagement stats

### Administrators
- User management with roles (admin, instructor, student)
- Category management
- Platform-wide analytics

### Platform
- Sessions in HttpOnly, Secure cookies (scripts can't read them) with CSRF protection, rotating refresh tokens with reuse detection, server-side logout and "log out everywhere"
- Email over SMTP: welcome, single-use password reset links, enrollment, receipts, grades, certificates (logged instead when SMTP isn't set)
- Paystack checkout for paid courses (off by default): hosted checkout, server-side verification, signed webhooks, receipts, real revenue reporting
- Instructor accounts are approved by an admin; self-sign-up always creates a student
- Role-based access control enforced in middleware on both the frontend and the API
- In-app notifications and media upload handling

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Nuxt 3 (Vue 3), Tailwind CSS, Lucide icons |
| Backend | FastAPI (Python 3), modular monolith |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev), PostgreSQL / Supabase (production) |
| Hosting | Vercel (website + API), Supabase (database + file storage) - see [DEPLOY.md](DEPLOY.md) |
| CI | GitHub Actions: all API tests on SQLite and Postgres, website build |
| Auth | JWT (PyJWT) with bcrypt password hashing |

## Architecture: Modular Monolith

The backend lives in `mini-services/lms-api` and is organized as bounded modules that share one process and one database:

```
mini-services/lms-api/app/
├── core/            # config, database, security, dependencies
├── shared/          # base model, utilities
└── modules/
    ├── auth/          # register, login, tokens, password reset
    ├── users/         # profiles and role management
    ├── courses/       # courses, modules, lessons, categories, announcements
    ├── enrollments/   # enrollment, progress, completion
    ├── assessments/   # quizzes, questions, attempts, grades
    ├── discussions/   # threaded course discussions
    ├── certificates/  # issuance and public verification
    ├── notifications/ # in-app notifications
    ├── media/         # file uploads
    └── analytics/     # platform and course analytics
```

Each module owns its models, service layer and router. Modules communicate through service functions rather than reaching into another module's tables, which keeps the monolith clean and makes a future split into services (or a multi-tenant SaaS rollout) straightforward.

## Deploying

See **[DEPLOY.md](DEPLOY.md)** for Supabase + Vercel + SMTP + Paystack, step by step.

## Getting Started

### Backend

```bash
cd mini-services/lms-api
pip install -r requirements.txt
cp .env.example .env   # optional, sane defaults
uvicorn app.main:app --port 8000
```

### Seed demo data

```bash
# from the repository root
npm run seed
```

### Frontend

```bash
npm install
npm run dev   # http://localhost:3000
```

The frontend talks to the API through the `/api` proxy. Direct browser access to the API is limited to the origins in `CORS_ORIGINS`.

### Tests

With the API running on a freshly seeded database:

```bash
cd mini-services/lms-api
AUTH_RATE_LIMIT_PER_MINUTE=1000 uvicorn app.main:app --port 8000   # tests log in many times
python3 test_api.py        # end-to-end feature checks
python3 test_security.py   # regression checks for the security fixes
python3 test_learning.py   # drip, prerequisites, notes, bookmarks, calendar, certificate PDFs
python3 test_live.py       # live classes + contact form
python3 test_platform.py   # cookie sessions, SMTP email, Paystack (self-contained; needs: pip install aiosmtpd)
```

### Demo accounts (after seeding)

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@infohive.demo | Admin123! |
| Instructor | sarah@infohive.demo | Teach123! |
| Student | michael@example.com | Study123! |

### Environment

Copy `mini-services/lms-api/.env.example` to `.env` and adjust as needed. Key settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LMS_DATABASE_URL` | `sqlite:///./data/lms.db` | Any SQLAlchemy URL; the schema is portable |
| `ENV` | `development` | `production` refuses to start without a real `SECRET_KEY` |
| `SECRET_KEY` | auto-generated in `data/.secret_key` (dev) | **Required** in production |
| `CORS_ORIGINS` | localhost:3000 | Origins allowed to call the API directly |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime (refresh rotates it) |
| `AUTH_RATE_LIMIT_PER_MINUTE` | `10` | Login/register/reset attempts per IP |
| `ALLOW_UNPAID_ENROLLMENT` | `false` | Payments aren't integrated; paid courses need manual enrollment |
| `MAX_UPLOAD_MB` | `50` | Upload size cap |

## Known limitations

- **Video protection** is deterrence, not DRM: it stops casual downloading and leaving the site, but someone using browser developer tools can still find the original link. Use a DRM video host (Bunny Stream, Mux, Vimeo OTT) when that matters. Vimeo's own controls can only be hidden on paid Vimeo plans; on free accounts they show but can't be clicked.
- **Payments** are off until `PAYSTACK_ENABLED=true`. While off, paid courses need manual enrollment by the instructor or an admin.
- **Rate limiting** is in-memory and per process/instance; use Redis (e.g. Upstash) if you see abuse.
- **Uploads on Vercel** are limited to ~4.5 MB per request; host videos on YouTube/Vimeo.
- **Schema changes** are applied by a small startup helper (`ensure_columns`). Adopt Alembic before production.

## SaaS-Ready Notes

- Ownership is always scoped by user and role at the service layer, which is the natural seam for multi-tenancy.
- All configuration is centralized in a single Settings object, so per-tenant settings, billing or plan limits can be added without re-architecting.
- The module boundaries (core / shared / modules) map one-to-one to potential microservices if the monolith ever needs to be split.
