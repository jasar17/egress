# FLS Checker

FLS Checker is a demo-ready Fire & Life Safety (FLS) egress-compliance review tool for commercial floor plans. A reviewer can open a project, inspect clause-cited egress findings on a plan, record a decision for each finding, and export a CSV summary.

This repository deliberately prioritizes a reliable demonstration workflow. The backend accepts PDF/DXF uploads, but returns known-good, deterministic overlays and findings rather than performing production-grade CAD analysis.

## Quick start

### Frontend

Requires Node.js.

```powershell
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

### Backend

Requires Python 3.11+ (a local virtual environment may already exist at `backend/.venv`).

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

The API runs on `http://127.0.0.1:8000`; interactive API docs are at `/docs`.

Run both services for persistence, upload, and export features. The frontend falls back to local demo findings when the API is unavailable.

## Current implementation

### Frontend: React + Vite

- `src/main.jsx` contains the entire current UI: project dashboard, review workspace, finding-detail panel, status actions, CSV export trigger, and upload modal.
- `src/styles.css` contains all styling and the responsive layout.
- **TASK 1 ✓ COMPLETED**: Upload modal sends files to `POST /projects/{id}/drawings` backend endpoint with occupancy_type and scale. Shows uploading state and error handling with spinner and error message display.
- **TASK 2 ✓ COMPLETED**: After successful upload, frontend polls `GET /drawings/{drawing_id}/status` every 1 second (max 30 attempts). On ready/failed status, auto-navigates to review screen. Stops polling on timeout.
- **TASK 3 ✓ COMPLETED**: Removed all hardcoded `drawing-al-noor-l06` references. Review workspace uses `currentDrawingId` state variable. Each upload sets new drawing ID; violations and elements fetched dynamically based on current ID.
- **TASK 4 ✓ COMPLETED**: Floor plan now fetches real element geometry from `GET /drawings/{id}/elements` and renders SVG polygon overlays (walls, rooms, doors). Seeded demo elements display deterministic overlay.
- **TASK 5 ✓ COMPLETED**: Added loading, error, and empty states to all API-driven screens:
  - Violations fetch: Shows spinner during load, error message if API fails (falls back to demo), empty state if no findings returned
  - Elements fetch: Loads silently, renders SVG if available
  - Added `violationsLoading` and `violationsError` state tracking
  - Styled loading spinner, error messages, and empty states with consistent design
  - Error messages display actual failure reason; empty state shows when drawing has no violations
- The review workspace fetches findings from `GET /drawings/{drawing_id}/violations` based on current drawing.
- Confirm, false-positive, and resolved actions persist through `PATCH /violations/{id}` when the backend is available.
- Export downloads a CSV from `GET /drawings/{drawing_id}/export`.
- **TASK 6 (Next)**: Add versioned demo asset and repeatable demo script.

### Backend: FastAPI + SQLite

- `backend/app/main.py` initializes a local SQLite database and seeds an Al Noor Business Centre, Level 06 demo drawing, floor-plan elements, two UAE FLS clauses, and four findings.
- `POST /projects/{project_id}/drawings` accepts `.pdf` and `.dxf`, stores the file under `backend/uploads/`, and schedules demo processing.
- Demo processing copies the seeded overlay geometry and findings to the uploaded drawing. It does not yet parse the file or calculate egress values.
- Runtime files are ignored by Git: `backend/data/`, `backend/uploads/`, and `backend/.venv/`.

## API routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` / `POST` | `/projects` | List or create projects |
| `POST` | `/projects/{id}/drawings` | Upload a PDF/DXF drawing |
| `GET` | `/drawings/{id}/status` | Check processing state |
| `GET` | `/drawings/{id}/elements` | Get overlay-ready element geometry |
| `GET` | `/drawings/{id}/violations` | Get code-cited findings |
| `PATCH` | `/violations/{id}` | Set `confirmed`, `false_positive`, or `resolved` |
| `GET` | `/drawings/{id}/export` | Download CSV review summary |

## Repository map

```text
src/                 React user interface
backend/app/main.py  FastAPI API, database schema, demo seed data
backend/requirements.txt
floor plan/          Reference commercial floor-plan PDF
FLS_MVP_PRD.pdf      Original MVP requirements
FLS_Demo_Backend_PRD.pdf  Demo API requirements/contract
PROJECT_CONTEXT.md   More detailed architecture and roadmap notes
```

## Recommended next work (Phase 1 Build Tasks)

1. **TASK 1 ✓ COMPLETED**: Upload modal sends files to backend with occupancy_type and scale parameters. Shows uploading/processing state with spinner and error handling.

2. **TASK 2 ✓ COMPLETED**: Polls `GET /drawings/{drawing_id}/status` after upload (1s intervals, 30 attempts max). Auto-navigates to review screen when ready.

3. **TASK 3 ✓ COMPLETED**: Removed hardcoded drawing IDs. Review workspace uses `currentDrawingId` state variable. All API calls use dynamic ID from current upload/selection.

4. **TASK 4 ✓ COMPLETED**: Floor plan renders real element geometry from `GET /drawings/{id}/elements` as SVG polygon overlays. Demo data provides deterministic visualization.

5. **TASK 5 ✓ COMPLETED**: All API-driven screens now have loading, error, and empty states:
   - Violations fetch shows spinner during load, error message on failure, empty state when no findings
   - Elements fetch loads silently and renders when available
   - Consistent styling with `loading-state`, `error-state`, and `empty-state` CSS classes
   - Fallback to demo data when API unavailable

6. **TASK 6 (Final)**: Commit a versioned, tested DXF (or PDF) demo file to the repo. Write a numbered demo walkthrough script documenting: upload flow, processing confirmation, review inspection, finding status changes, and export output.

## Longer-term production work

- Parse DXF content with `ezdxf` and classify walls, doors, rooms, and exits.
- Build walkable paths with NetworkX; measure travel distance and exit capacity using Shapely plus drawing scale.
- Evaluate calculated values against an expanded UAE FLS code library and persist actual rule results.
- Replace SQLite/local storage with PostgreSQL/object storage; add migrations, authentication, authorization, tenant isolation, background jobs, retries, observability, validation, and deployment configuration.
- Harden PDF/vector/CV extraction for real drawings and produce a polished PDF report in addition to CSV.

## Handoff notes for another AI

- Preserve the demo-first behavior unless explicitly asked to implement real CAD processing; it keeps the presentation predictable.
- The frontend has a fallback for unavailable APIs, so API errors can be visually masked. Test with the backend running when changing integration code.
- The backend CORS allowlist currently permits only `localhost:5173` and `127.0.0.1:5173`; update it if the frontend port or deployment origin changes.
- `PROJECT_CONTEXT.md` has additional rationale and a fuller roadmap. The PRDs are the source of truth for intended product and demo scope.
