# FLS Checker Backend Service

FastAPI service implementing the real Fire & Life Safety (FLS) compliance analysis and multi-floor decoding engine.

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **API URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Database**: SQLite database stored automatically at `backend/data/fls_demo.db`.

## 🌐 Live Production Deployment

- **Live Cloud API**: [https://egressandco.onrender.com](https://egressandco.onrender.com)
- **Live Swagger Documentation**: [https://egressandco.onrender.com/docs](https://egressandco.onrender.com/docs)
- **Production Frontend (Vercel)**: [https://egress-jade.vercel.app/](https://egress-jade.vercel.app/)
- **Persistent Storage**: Supabase PostgreSQL integration via SSL pooler (backing `drawing_files` binary storage and table persistence across Render container spin-downs).

## Core API Endpoints

1. `GET /projects` — Returns active project workspaces and drawings.
2. `POST /projects/{id}/drawings` — Uploads PDF/DXF drawings with dynamic scale, occupancy classification, and sprinkler status.
3. `GET /drawings/{id}` — Returns drawing details, active floor page, and complete multi-floor summary.
4. `GET /drawings/{id}/pages` — Returns detected floor levels with live error counts (`violations_count`) and compliance status.
5. `GET /drawings/{id}/multi-floor-summary` — Multi-floor audit hub returning decoded geometry, room summaries, occupant loads, max travel distances, and error lists for every floor plan in the document.
6. `POST /drawings/{id}/page` — Switches the active floor page with instant re-extraction and rule evaluation.
7. `PATCH /drawings/{id}/config` — Dynamically updates occupancy type or sprinkler status with live rule re-evaluation.
8. `GET /drawings/{id}/elements` — Serves overlay-ready GeoJSON FeatureCollection (polygons, walls, doors, exits) in 0..100% coordinate space.
9. `GET /drawings/{id}/violations` — Serves deterministic, UAE code-cited egress violations with exact coordinates.
10. `PATCH /violations/{id}` — Records review decisions (`confirmed`, `false_positive`, `resolved`, `open`).
11. `GET /drawings/{id}/export` — Generates and downloads structured compliance review CSV.
12. `GET /code-clauses` — Lists 170 authentic UAE Fire and Life Safety Code clauses.

## Core Processing Pipeline

1. **Geometry Extraction (`dxf_parser.py` & `pdf_parser.py`)**:
   - **DXF files**: parsed via `ezdxf` + `shapely` with layer decomposition (`WALLS`, `DOORS`, `EXITS`, `ROOM_BOUNDARIES`) and text matching.
   - **PDF files**: parsed via `pymupdf` extracting vector lines, polylines, room polygons, doors, and title annotations (supports `DXB-2026-88A` custom architectural drawings and multi-page floor plan sets).
   - **0..100% Unified Coordinate Pipeline**: All spatial elements are normalized to true page percentage values for exact overlay registration.
2. **Occupant Load Calculation (`occupant_load.py`)**:
   - Computes occupant loads dynamically using UAE FLS Table 3.13 density factors (`9.3 m²/person` regular office, `4.6 m²/person` concentrated workstation, `1.4 m²/person` conference/dining, `27.9 m²/person` storage) from actual physical room geometry.
3. **Egress Path Analysis (`path_analysis.py`)**:
   - Constructs shortest-path walkable network via `networkx` connecting room centroids, doors, circulation corridors, and emergency exit stairs.
4. **FLS Rules Engine (`rules_engine.py`)**:
   - Evaluates travel distance limits (sprinklered 91m / non-sprinklered 61m), single-exit room allowances (`UAE-FLS-3.19-BUS-SINGLE-DOOR` for occupant loads <100p with exterior discharge <=30m), 2-door room area thresholds (280 m²), exit remoteness, corridor widths (1200mm), and stair exit counts citing official UAE clauses.
5. **Multi-Floor Summary Engine (`main.py:compute_multi_floor_summary`)**:
   - Automatically decodes every page of multi-page PDFs to provide building-wide compliance rollups.

## Automated Test Suites

```powershell
# 1. 20-suite core backend API tests
.\.venv\Scripts\python.exe test_api.py

# 2. Dubai 5-Floor regression test suite (prints explicit per-room occupant loads)
.\.venv\Scripts\python.exe test_dubai_regression.py

# 3. Multi-floor PDF decoding and error rollup test
.\.venv\Scripts\python.exe test_multi_floor_summary.py

# 4. Full 12-floor building validation runner (DXF + PDF)
.\.venv\Scripts\python.exe validate_all_floors.py

# 5. Coordinate precision integration test
.\.venv\Scripts\python.exe test_coordinate_accuracy.py
```
