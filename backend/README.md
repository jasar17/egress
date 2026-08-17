# FLS Checker demo backend

FastAPI service implementing the demo API in `FLS_Demo_Backend_PRD.pdf`.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`.
It creates `backend/data/fls_demo.db` and `backend/uploads/` automatically. Set `FLS_DATABASE_PATH` to move the SQLite database. The storage boundary is deliberately isolated so it can be replaced with PostgreSQL/S3 for the full MVP.

## Demo flow

1. `GET /projects` returns the seeded Al Noor project and demo drawing.
2. `GET /drawings/{drawing_id}/elements` serves overlay-ready GeoJSON-like feature data.
3. `GET /drawings/{drawing_id}/violations` serves deterministic, clause-cited flags.
4. `PATCH /violations/{violation_id}` records `confirmed`, `false_positive`, or `resolved`.
5. `GET /drawings/{drawing_id}/export` downloads the review CSV.

Upload accepts `.dxf` and `.pdf`. DXF parsing uses `ezdxf` when installed; a known-good demo floor geometry is always generated as a safe fallback, so the review flow remains demonstrable for the pre-tested drawing.
