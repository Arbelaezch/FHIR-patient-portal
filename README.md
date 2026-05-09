# FHIR Patient Portal

A patient-facing health dashboard that authenticates using the SMART on FHIR standard and displays real patient data via a FHIR R4 API.

Built as a portfolio project to demonstrate healthcare domain knowledge and full-stack development skills relevant to EHR/EMR companies.

![Demo](demo.gif)

## Overview

This project implements the **SMART App Launch Framework** — the OAuth2-based standard used by real EHR systems like Epic and Cerner to authorize third-party applications to access patient data. The app authenticates against the SMART Health IT reference sandbox, retrieves patient health records, and displays them in a clean dashboard UI.

**What this demonstrates:**
- SMART on FHIR OAuth2 with PKCE (the modern standard for patient-facing apps, no client secret required)
- Secure server-side session management — FHIR access tokens never touch the browser
- FHIR R4 resource parsing for Patient, Observation, MedicationRequest, and Condition
- Real integration against a FHIR R4 server with synthetic patient data

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, CSS Modules |
| Backend | FastAPI (Python 3.12), asyncpg |
| Auth | SMART on FHIR, PKCE, Starlette SessionMiddleware |
| Session Store | Redis |
| Database | PostgreSQL 16 |
| Container | Docker, Docker Compose |
| FHIR | SMART Health IT R4 sandbox via `fhir.resources` |

## Architecture

```
frontend/                          backend/
Next.js (port 3000)                FastAPI (port 8000)
        │                                  │
        │  1. GET /auth/login              │
        │ ────────────────────────────────>│
        │                                  │ 2. Generate PKCE pair
        │                                  │    Store verifier in Redis
        │                                  │    Redirect to SMART auth URL
        │ <────────────────────────────────│
        │
        │  3. User selects a patient
        │     in the SMART launcher
        │
        │  4. Launcher redirects to /auth/callback?code=...
        │ ────────────────────────────────>│
        │                                  │ 5. Exchange code + verifier
        │                                  │    for access token
        │                                  │    Store token in Redis
        │                                  │    Set signed session cookie
        │ <────────────────────────────────│
        │
        │  6. GET /fhir/Patient/{id}       │
        │ ────────────────────────────────>│
        │                                  │ 7. Retrieve token from Redis
        │                                  │    Proxy request to FHIR API
        │                                  │    Return FHIR resource
        │ <────────────────────────────────│
```

The access token is stored server-side in Redis and never sent to the browser. The browser holds only a signed session cookie that references the Redis entry.

## Project Structure

```
FHIR-patient-portal/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middleware, router registration
│   │   ├── config.py                # Pydantic settings (loaded from .env)
│   │   ├── database.py              # Async SQLAlchemy setup
│   │   ├── routes/
│   │   │   ├── auth/
│   │   │   │   └── smart.py         # SMART on FHIR auth flow (login, callback, session, logout)
│   │   │   └── fhir/
│   │   │       └── proxy.py         # FHIR resource proxy endpoints
│   │   └── services/
│   │       └── session_store.py     # Redis session store wrapper
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.js              # Dashboard — displays all four FHIR resource cards
│   │   │   ├── profile/
│   │   │   │   └── page.js          # Patient profile page
│   │   │   └── login/
│   │   │       └── page.js          # Login page — initiates SMART on FHIR flow
│   │   ├── components/
│   │   │   └── ResourceCard.js      # Reusable FHIR resource display card
│   │   └── lib/
│   │       └── fhirClient.js        # API client for backend auth and FHIR endpoints
│   └── .env.local
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd FHIR-patient-portal
   ```

2. **Configure the backend**
   ```bash
   # backend/.env
   DATABASE_URL=postgresql+asyncpg://fhir_user:fhir_password@postgres:5432/fhir_portal
   SECRET_KEY=your-secret-key-change-in-production
   REDIS_URL=redis://redis:6379
   EPIC_CLIENT_ID=my_fhir_portal
   FRONTEND_URL=http://localhost:3000
   ```

3. **Configure the frontend**
   ```bash
   # frontend/.env.local
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

4. **Start the backend services**
   ```bash
   docker-compose up --build
   ```

5. **Start the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Open the app**

   Navigate to [http://localhost:3000](http://localhost:3000) and click **Connect** to authenticate via the SMART launcher and select a synthetic test patient.

## Auth Flow Detail

This app implements the **SMART App Launch (Standalone Launch)** pattern with **PKCE**:

1. `/auth/login` — generates a `code_verifier` (random string) and `code_challenge` (SHA-256 hash of verifier), stores the verifier in Redis, redirects the user to the SMART authorization endpoint
2. User selects a synthetic test patient in the SMART launcher
3. `/auth/callback` — the launcher redirects here with an authorization `code`; the backend retrieves the verifier from Redis, exchanges `code + verifier` for an access token, stores the token in Redis, sets a signed session cookie
4. All subsequent FHIR requests go through the backend proxy, which retrieves the token from Redis and injects it as a `Bearer` token in the upstream FHIR request
5. `/auth/logout` — deletes the Redis entry and clears the session cookie

PKCE eliminates the need for a client secret, which is the correct approach for patient-facing apps where the client cannot securely store a secret. This is the same auth pattern used by production integrations with Epic, Cerner, and other major EHR vendors.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/auth/login` | Initiate SMART on FHIR flow |
| `GET` | `/auth/callback` | OAuth2 callback — exchange code for token |
| `GET` | `/auth/session` | Check authentication status |
| `POST` | `/auth/logout` | Clear session |
| `GET` | `/fhir/Patient/{id}` | Fetch Patient resource |
| `GET` | `/fhir/Observation` | Fetch Observations |
| `GET` | `/fhir/MedicationRequest` | Fetch MedicationRequests |
| `GET` | `/fhir/Condition` | Fetch Conditions |
| `GET` | `/health` | Backend health check |

## Development

```bash
# View backend logs
docker-compose logs -f backend

# Restart backend only (after code changes)
docker-compose restart backend

# Reset all data (clears PostgreSQL and Redis volumes)
docker-compose down -v
docker-compose up --build

# Open Redis CLI
docker-compose exec redis redis-cli

# List active sessions
docker-compose exec redis redis-cli keys "*"
```