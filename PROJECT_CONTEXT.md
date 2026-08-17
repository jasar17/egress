# FLS Checker - Project Context

## Purpose

FLS Checker is a demo-ready Fire & Life Safety (FLS) egress-compliance review tool. A user can upload a commercial floor drawing, inspect extracted floor-plan elements and code-cited egress findings, review each finding, and export a summary.

The implementation follows the scope in `FLS_Demo_Backend_PRD.pdf`: demonstrate a convincing, deterministic workflow for a pre-tested commercial-office drawing before expanding toward a production MVP.

## Project structure

```text
.
├── src/
│   ├── main.jsx                 # React dashboard and compliance-review UI
│   └── styles.css               # UI styling and responsive layout
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI routes, SQLite schema, seed data
│   ├── requirements.txt         # Python API dependencies
│   └── README.md                # Backend setup and endpoint guide
├── FLS_MVP_PRD.pdf              # Broader MVP product requirements
├── FLS_Demo_Backend_PRD.pdf     # Demo backend requirements and API contract
├── package.json                 # Vite/React frontend scripts and dependencies
├── .gitignore                   # Excludes generated runtime files and dependencies
└── PROJECT_CONTEXT.md           # This handoff/context document
```

Runtime-created, ignored folders:

- `backend/data/` - SQLite database (`fls_demo.db`)
- `backend/uploads/` - uploaded DXF/PDF files
- `backend/.venv/` - local Python virtual environment
- `dist/` and `node_modules/` - frontend build/dependency output

## Current progress

### Frontend

- React/Vite interface is implemented in `src/main.jsx`.
- Includes dashboard, upload modal, interactive floor-plan review, finding selection, review actions, and export action.
- The review screen now calls the backend at `http://127.0.0.1:8000`:
  - Loads seeded violations from `GET /drawings/drawing-al-noor-l06/violations`.
  - Saves review actions with `PATCH /violations/{id}`.
  - Downloads the backend-generated CSV via `GET /drawings/drawing-al-noor-l06/export`.
- A local UI fallback remains if the API is unavailable.
- `npm run build` passes.

### Backend

- FastAPI service is implemented in `backend/app/main.py`.
- SQLite is initialized automatically on startup and seeded with:
  - Al Noor Business Centre project
  - Level 06 commercial-office drawing
  - floor-plan overlay elements (walls, rooms, doors, exits)
  - four deterministic UAE-code-cited violations
  - a small static UAE FLS clause table
- Implemented API routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `GET` | `/projects` | List projects |
| `POST` | `/projects` | Create a project |
| `POST` | `/projects/{id}/drawings` | Upload DXF/PDF and start demo processing |
| `GET` | `/drawings/{id}/status` | Poll drawing status |
| `GET` | `/drawings/{id}/elements` | Return GeoJSON-like overlay data |
| `GET` | `/drawings/{id}/violations` | Return clause-cited findings |
| `PATCH` | `/violations/{id}` | Mark a finding confirmed, false positive, or resolved |
| `GET` | `/drawings/{id}/export` | Download CSV review summary |

- Live checks completed:
  - backend health endpoint returns `200 OK`
  - frontend returns `200 OK`
  - seeded violations endpoint returns four findings

## Architectural decisions

### Demo-first, deterministic processing

The backend favors a reliable demonstration path over arbitrary-drawing robustness. Uploads are accepted and persisted, then receive pre-tested overlay and violation data. This meets the demo PRD's cached-fallback requirement and avoids a fragile live CAD/CV pipeline during a presentation.

### Python/FastAPI backend

FastAPI was selected by the PRD because the future extraction, geometry, and code-rule work is Python-friendly. The API shape already matches the intended production workflow, so frontend consumers do not need to be redesigned later.

### SQLite by default, isolated persistence boundary

SQLite provides zero-configuration local development and demo reliability. The database path can be changed with `FLS_DATABASE_PATH`; moving to PostgreSQL later should preserve the entities and route contracts, while replacing only the persistence implementation.

### Local files for demo storage

Uploaded source drawings are saved under `backend/uploads/`. This is intentional for the demo. S3/object storage, access controls, and tenant isolation are deferred.

### GeoJSON-like overlay contract

Extracted elements and violation geometry are returned as coordinate-bearing JSON. The frontend can render that directly on a plan/canvas and remains insulated from parser internals.

### Static code-clause reference data

The demo uses a compact, hand-curated code table. Findings cite concrete UAE FLS clause references instead of using LLM-generated explanations, making the demo traceable and deterministic.

### No authentication or async queue yet

The demo is single-user and processes one file at a time. Authentication, authorization, background job infrastructure, and multi-tenant concerns are explicitly outside the current scope.

## Run locally

Backend:

```powershell
.\backend\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --reload
```

Frontend:

```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```

- Website: `http://127.0.0.1:5173`
- API docs: `http://127.0.0.1:8000/docs`

## Remaining tasks

### Immediate demo improvements

- Connect the upload modal to `POST /projects/{id}/drawings` and poll its status endpoint.
- Render the `/elements` response rather than the current CSS-drawn floor plan.
- Show the uploaded drawing and its extracted overlay in the review view.
- Add visible loading, processing, failed, and empty states.
- Add automated API tests for seed data, upload, status updates, and CSV export.
- Add a pre-tested DXF file to versioned demo assets (or document where it is securely stored).

### Replace demo fixtures with actual CAD processing

- Use `ezdxf` to parse the selected DXF's layers, lines, polylines, and block references.
- Classify walls, doors, rooms, and exits with layer/block conventions and demo-file overrides.
- Build a walkable graph with NetworkX and calculate nearest-exit travel paths.
- Use Shapely and drawing scale for measured geometry.
- Evaluate actual calculated values against the clause table and persist the resulting flags.

### Production MVP work

- Replace SQLite with PostgreSQL and add migrations.
- Add authentication, user/project authorization, and multi-tenant isolation.
- Move drawing storage to object storage and validate file-size/content limits.
- Add a background queue for non-blocking processing and durable retries.
- Expand the UAE FLS clause library and support more occupancy types.
- Add PDF/vector/CV extraction hardening for real-world drawings.
- Produce a polished PDF export in addition to CSV.
- Add observability, validation, error handling, security review, and deployment configuration.
