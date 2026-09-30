# LearnHub LMS

A full-featured, industry-standard Learning Management System built as a **modular monolith**: a Nuxt 3 frontend, a FastAPI backend, and SQLAlchemy 2.0 ORM over a portable schema (SQLite by default, PostgreSQL-ready).

## Features

### Students
- Course catalog with categories, search and filtering
- Course preview pages and secure enrollment
- Learning experience with video lessons, rich text content and progress tracking
- Quizzes with auto-grading, multiple attempts and instant feedback
- Grades and certificates with public verification pages
- Course announcements and threaded discussions

### Instructors
- Course builder for modules, lessons and video uploads
- Student management and gradebook
- Announcements and per-course analytics
- Instructor dashboard with engagement stats

### Administrators
- User management with roles (admin, instructor, student)
- Category management
- Platform-wide analytics

### Platform
- JWT authentication with access and refresh tokens plus a password reset flow
- Role-based access control enforced in middleware on both the frontend and the API
- In-app notifications and media upload handling

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Nuxt 3 (Vue 3), Tailwind CSS, Lucide icons |
| Backend | FastAPI (Python 3), modular monolith |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev), PostgreSQL-ready |
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

The frontend talks to the API through the `/api` proxy, and the API enables permissive CORS for development.

### Demo accounts (after seeding)

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@learnhub.io | Admin123! |
| Instructor | sarah@learnhub.io | Teach123! |
| Student | michael@example.com | Study123! |

### Environment

Copy `mini-services/lms-api/.env.example` to `.env` and adjust as needed. Key settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LMS_DATABASE_URL` | `sqlite:///./data/lms.db` | Any SQLAlchemy URL; the schema is portable |
| `SECRET_KEY` | dev value | Set a strong random value in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Access token lifetime |
| `MAX_UPLOAD_MB` | `50` | Upload size cap |

## SaaS-Ready Notes

- Ownership is always scoped by user and role at the service layer, which is the natural seam for multi-tenancy.
- All configuration is centralized in a single Settings object, so per-tenant settings, billing or plan limits can be added without re-architecting.
- The module boundaries (core / shared / modules) map one-to-one to potential microservices if the monolith ever needs to be split.
