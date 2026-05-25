# NetworkPilot

`NetworkPilot` is an Odoo 18 addon with an embedded React frontend for personal CRM workflows.

## What is inside

- Odoo models and controllers for contacts, reminders, interactions, integrations, relationship graph, and messaging
- React + TypeScript SPA served by Odoo from `/app/`
- AI helper layer for contact strategy and meeting planning
- Business card OCR endpoint backed by an external AI provider

## Project structure

- `controllers/` HTTP routes for auth, CRM API, SPA shell, graph, chats, and AI endpoints
- `models/` Odoo ORM models
- `services/` lightweight AI service layer
- `frontend_source/` Vite frontend source
- `static/app/` built frontend assets served by Odoo
- `views/`, `security/` Odoo XML views and access rules

## Local run

1. Start the stack:

```powershell
docker compose up -d
```

2. Open Odoo on `http://localhost:8076`.
3. Install the addon `Networkpilot` into your working database.
4. Open the frontend at `http://localhost:8076/app/`.

## Frontend build

If you change files in `frontend_source/`, rebuild the frontend:

```powershell
cd frontend_source
npm install
npm run build
```

Then copy the built assets from `frontend_source/dist/` into `static/app/`.

## AI configuration

Contact strategy works with a lightweight local heuristic fallback.

Business card OCR and external model calls require these environment variables:

- `NETWORKPILOT_AI_ENDPOINT`
- `NETWORKPILOT_AI_API_KEY`
- `NETWORKPILOT_AI_MODEL`

Without them, `/api/v1/ai/business-card-scan` returns `503`.

## Main routes

- `/app/` React application entry
- `/api/v1/auth/*` session auth API
- `/api/v1/contacts` contacts API
- `/api/v1/network/*` contact graph and relationships
- `/api/v1/messages/*` chats between contacts
- `/api/v1/ai/*` AI helpers
