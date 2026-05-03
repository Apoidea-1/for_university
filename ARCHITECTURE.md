# NetWorkPilot Architecture

## 1. Stack

- Frontend: React, TypeScript, Vite, React Router, React Hook Form, Zod, TanStack Query, Tailwind CSS, Recharts
- Backend: FastAPI, SQLAlchemy 2.x, Pydantic, Alembic, JWT auth
- Database: PostgreSQL
- Infrastructure: Docker Compose, `.env` configuration
- Testing: pytest integration tests for auth, contacts, reminders, analytics
- AI layer: isolated `AIRecommendationService` with mock heuristics and persistence hook via `ai_suggestions`

## 2. Architectural shape

- Monorepo with independent `frontend` and `backend`
- Backend uses layered structure: `api` -> `services` -> `repositories` -> `models/db`
- Frontend uses app shell + domain features: auth, contacts, reminders, analytics, integrations
- API contract is fully namespaced under `/api/v1`
- AI is abstracted into a service module so a real provider can replace mock logic without changing routes or UI flow

## 3. Repository structure

```text
networkpilot/
  frontend/
    src/
      app/
      pages/
      features/
      widgets/
      components/
      shared/
      api/
      hooks/
      types/
    Dockerfile
    package.json
    tailwind.config.ts
    vite.config.ts
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      repositories/
      tests/
    alembic/
    Dockerfile
    requirements.txt
    alembic.ini
  docker-compose.yml
  .env.example
  ARCHITECTURE.md
  README.md
```

## 4. Domain model

### Core entities

- `users`: platform accounts, owner of all private data
- `contacts`: personal CRM records with professional context, importance, and notes
- `categories`: user-scoped or global contact grouping
- `tags`: user-scoped or global free-form labels
- `contact_tags`: many-to-many bridge between contacts and tags
- `interactions`: time-based history of meetings, calls, messages, projects
- `reminders`: follow-up tasks linked to user and optionally a contact
- `ai_suggestions`: persisted AI output for metadata and next actions
- `integrations`: future integration state for Google Calendar, LinkedIn, Telegram
- `activity_logs`: audit-style history for product analytics and traceability

### Key relationships

- `users 1 -> many contacts`
- `users 1 -> many reminders`
- `users 1 -> many integrations`
- `contacts many -> 1 categories`
- `contacts many <-> many tags` via `contact_tags`
- `contacts 1 -> many interactions`
- `contacts 1 -> many reminders`
- `contacts 1 -> many ai_suggestions`

### Referential behavior

- User deletion cascades to private workspace data
- Contact deletion cascades to interactions, reminders, AI suggestions, tag links
- Category deletion sets `contacts.category_id` to `NULL`
- Tag deletion cascades only bridge rows

## 5. Key API surface

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Contacts

- `GET /api/v1/contacts`
- `POST /api/v1/contacts`
- `POST /api/v1/contacts/quick-add`
- `GET /api/v1/contacts/{id}`
- `PATCH /api/v1/contacts/{id}`
- `DELETE /api/v1/contacts/{id}`

### Interactions

- `GET /api/v1/contacts/{id}/interactions`
- `POST /api/v1/contacts/{id}/interactions`
- `DELETE /api/v1/interactions/{id}`

### Reminders

- `GET /api/v1/reminders`
- `POST /api/v1/reminders`
- `PATCH /api/v1/reminders/{id}`
- `DELETE /api/v1/reminders/{id}`

### AI

- `POST /api/v1/ai/suggest-contact-metadata`
- `POST /api/v1/ai/suggest-next-action`

### Analytics

- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/categories`
- `GET /api/v1/analytics/stale-contacts`

### Integrations

- `GET /api/v1/integrations`
- `POST /api/v1/integrations/{provider}/connect-mock`

### Lookups

- `GET /api/v1/categories`
- `POST /api/v1/categories`
- `GET /api/v1/tags`
- `POST /api/v1/tags`

## 6. Primary user scenarios

1. Register or log in and immediately receive default categories, tags, and integration stubs.
2. Add a contact fast from dashboard or contacts page with just name, source, category, and note.
3. Open full contact form, enrich metadata, ask AI for category/tags/summary, and save.
4. Open contact profile, log interactions, generate next-action suggestion, and create follow-up reminder.
5. Review reminders by status and mark completed work.
6. Inspect dashboard and analytics to understand contact growth, interaction volume, stale relationships, and category mix.

## 7. Why this MVP scales cleanly

- Backend business logic is not trapped inside route handlers.
- Frontend API contract is centralized in typed modules.
- AI provider swap is localized to `AIRecommendationService`.
- Integrations already have persistent state and UI, so real OAuth/sync flows can replace mock connect later.
