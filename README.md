# Clinic Inbox Agent

AI-assisted triage dashboard for a clinic-style shared inbox.

This project simulates how a clinic team might manage incoming patient messages: an AI “agent” classifies each message by **urgency** and **category** (billing, scheduling, clinical, other) and proposes a **suggested action**. Staff can then **confirm** or **override** the AI suggestion from a simple web UI.

> Backend: FastAPI + SQLite (PostgreSQL-ready)  
> Frontend: Next.js + Tailwind CSS

---

## Features

- 📨 **Shared inbox view**  
  List of incoming patient messages with subject, snippet, channel, and status.

- 🤖 **AI triage agent**  
  Backend endpoint that classifies a message into:
  - urgency: `low | medium | high`
  - route/category: `billing | scheduling | clinical | other`
  - suggested action text

- ✅ **Confirm / override workflow**
  - “Ask agent” button triggers triage for a message.
  - Staff can **confirm** the suggestion or **override** it (e.g., change urgency/route).

- 📊 **Auditability**
  - Every triage run is stored as an `AgentRun` row (model name, prompt, raw output, confidence).
  - Each triage decision is stored as a `TriageAction` row linked to the original message.

- 🧪 **Fake LLM mode + real LLM ready**
  - By default, the app uses a simple **fake response** (no external API calls).
  - Optional integration with OpenAI (or compatible) by setting `OPENAI_API_KEY`.

---

## Tech Stack

**Backend**

- [FastAPI](https://fastapi.tiangolo.com/) – REST API framework
- [SQLAlchemy](https://www.sqlalchemy.org/) – ORM & database models
- [Pydantic v2](https://docs.pydantic.dev/) & `pydantic-settings` – data validation & config
- **SQLite** as the default database (file-based, `clinic_inbox.db`)  
  – easily switchable to **PostgreSQL** by changing the `DATABASE_URL` (`postgresql+psycopg2://…`)

**Frontend**

- [Next.js 16](https://nextjs.org/) (App Router, TypeScript)
- React
- [Tailwind CSS](https://tailwindcss.com/) – styling & layout

**LLM / “Agent”**

- Pluggable triage service:
  - default: fake / heuristic response (no network)
  - optional: OpenAI client (e.g. `gpt-4o-mini`) when API key is configured

---

## Architecture

High-level flow:

1. A **Message** row represents an inbound patient communication.
2. The frontend calls `POST /api/triage/` with a `message_id`.
3. Backend:
   - loads the message from the database
   - calls the triage service (fake LLM or OpenAI)
   - writes an **AgentRun** row (full input/output)
   - writes a **TriageAction** row (urgency, route, suggested action)
   - updates the message `status` from `new` → `triaged`
4. Frontend reloads `/api/messages` and shows:
   - urgency pill (`LOW | MEDIUM | HIGH`)
   - category pill (`billing | scheduling | clinical | other`)
   - current triage status (`pending | confirmed | overridden`)

---

## Project Structure

```txt
clinic-inbox-agent/
  backend/
    app/
      __init__.py
      main.py         # FastAPI app, CORS, router wiring
      database.py     # SQLAlchemy engine & SessionLocal (SQLite by default)
      models.py       # Patient, Message, AgentRun, TriageAction
      schemas.py      # Pydantic models for requests/responses
      deps.py         # DB session dependency
      routers/
        __init__.py
        messages.py   # /api/messages (list & create)
        triage.py     # /api/triage (triage, confirm, override)
      services/
        __init__.py
        llm.py        # triage_message_with_llm (fake + OpenAI mode)
    .env              # backend config (DATABASE_URL, OPENAI_API_KEY, etc.)
    clinic_inbox.db   # SQLite database (auto-created)
  frontend/
    app/
      page.tsx        # main dashboard UI
    lib/
      api.ts          # API base URL helper
    types.ts          # shared TypeScript interfaces
    .env.local        # frontend config (NEXT_PUBLIC_API_BASE_URL)
  README.md
  LICENSE


---

## API Overview

### Health check

* `GET /health` → `{ "status": "ok" }`

### Messages

* `GET /api/messages/`
  Returns an array of messages, each including latest triage + agent run summary.

* `POST /api/messages/`
  Create a new message (e.g., from a form or seed script).

  ```json
  {
    "subject": "Refill request for blood pressure medication",
    "body": "Hi, I am running low on my prescription. Can I get a refill?",
    "channel": "portal",
    "patient_id": null
  }
  ```

### Triage

* `POST /api/triage/`
  Trigger triage for a specific message.

  **Request**

  ```json
  {
    "message_id": 1
  }
  ```

  **Response (simplified)**

  ```json
  {
    "message": { "...": "..." },
    "triage": {
      "id": 3,
      "urgency": "medium",
      "route": "clinical",
      "status": "pending",
      "suggested_summary": "[MEDIUM] clinical — Refill request for blood pressure medication"
    },
    "agent_run": {
      "id": 5,
      "model_name": "gpt-4o-mini",
      "confidence": 0.7
    }
  }
  ```

* `POST /api/triage/{triage_id}/confirm`
  Mark a triage suggestion as confirmed.

* `POST /api/triage/{triage_id}/override`
  Override a triage suggestion (urgency/route/summary) and mark as `overridden`.

---

## Getting Started

### Prerequisites

* Python 3.10+ (tested with 3.12)
* Node.js 18+ (recommended)
* npm or pnpm
* (Optional) OpenAI API key if you want real LLM classification
* (Optional) PostgreSQL if you want to swap away from SQLite

---

### 1. Backend setup

From the repo root:

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or on WSL / macOS:
# source .venv/bin/activate

pip install -r requirements.txt
# or if not present:
# pip install fastapi uvicorn[standard] sqlalchemy pydantic-settings python-dotenv openai
```

Create `backend/.env`:

```env
# SQLite (default, no Docker needed)
DATABASE_URL=sqlite:///./clinic_inbox.db

# LLM config
OPENAI_API_KEY=        # optional; leave empty to use fake mode
LLM_MODEL=gpt-4o-mini
LLM_FAKE=true          # true = use fake response, no external calls
```

> To switch to PostgreSQL later, just change `DATABASE_URL` to something like
> `postgresql+psycopg2://user:password@localhost:5432/clinic_inbox`.

Run DB migrations (tables are created automatically on startup):

```bash
uvicorn app.main:app --reload
```

On first run, SQLAlchemy will create `clinic_inbox.db` and all tables.

---

### 2. Seed some demo messages

From `backend` with the virtualenv active:

```bash
python -m app.seed
```

This will insert a few example messages:

* Refill request (portal)
* Billing question (email)
* New chest pain / shortness of breath (phone)

---

### 3. Frontend setup

Open a new terminal at the repo root:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
```

Visit: **[http://localhost:3000](http://localhost:3000)**

You should see:

* The **Clinic Inbox Agent** dashboard.
* One row per seeded message.
* “Ask agent” button per message.

Click **Ask agent** → backend triages the message → UI updates with urgency + route pills and status.

---

## Running both services together

1. **Backend**

   ```bash
   cd backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload
   ```

2. **Frontend**

   ```bash
   cd frontend
   npm run dev
   ```

3. Open `http://localhost:3000` in your browser.

---

## Future Improvements

Some ideas for next iterations:

* **Real LLM triage** by turning off `LLM_FAKE` and using OpenAI or another provider.
* **Message composer** on the frontend to create new messages instead of only using seed data.
* **Authentication & roles** (e.g., staff vs admin).
* **Pagination & filters** for the inbox (by status, urgency, category).
* **PostgreSQL + Docker Compose** for a more production-like environment.
* **Background jobs** (e.g., triage queue, scheduled re-triage).

---