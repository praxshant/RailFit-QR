# Indian Railways – Track Fittings QR System (SIH 2025)

An end-to-end QR-based identification and quality monitoring system for Indian Railways track fittings (Elastic Rail Clips, Rail Pads, Liners, Sleepers). The system enables:

- Laser-ready QR code generation for each item/lot
- Mobile-friendly scan and verification (upload-based in MVP; camera mode ready to add)
- Role-based dashboards (Manufacturer, Vendor, Railway Official)
- AI-powered quality/maintenance insights
- Integration stubs for UDM (ireps.gov.in) and TMS (irecept.gov.in) via configurable endpoints

This project aligns with SIH 2025 Problem Statement ID 25021.

## Features

- QR-only, no barcode dependencies
- Secure JWT-based auth with role enforcement
- Indian Railways-themed UI with separate dashboards per role
- Advanced QR scanning with preprocessing for metal surfaces
- AI quality/reliability heuristics and recommendations
- Database-backed inventory with search and summaries

## Repository Layout

```
railway-barcode-system/
├─ backend/
│  ├─ app.py                          # Flask API (QR-only, role-based)
│  ├─ middleware/auth.py              # Token decorator (legacy-compatible)
│  ├─ models/railway_item.py          # SQLAlchemy model (uses qr_ref)
│  ├─ services/
│  │  ├─ qr_generator.py              # Generate styled QR images
│  │  ├─ advanced_qr_scanner.py       # Upload-based QR scan w/ preprocessing
│  │  ├─ ai_analyzer.py               # AI heuristics
│  │  ├─ auth_service.py              # JWT issuance + role middleware
│  │  └─ udm_tms_integration.py       # UDM/TMS sync stubs using qr_ref
│  └─ utils/
│     └─ database.py                  # DB init/session (sqlite:///railway_qr.db)
├─ frontend/
│  ├─ public/
│  │  ├─ index.html                   # Indian Railways UI
│  │  └─ styles.css                   # Theme
│  └─ src/
│     └─ app.js                       # Role-based SPA logic (QR-only)
├─ database/
│  ├─ schema.sql                      # Optional schema (SQLAlchemy also creates tables)
│  └─ seed_data.sql                   # Seed row for demo
├─ ai_models/                         # Placeholder folder for AI assets
├─ scripts/                           # Utility scripts (legacy barcode files removed)
├─ requirements.txt                   # Python backend dependencies
├─ docker-compose.yml (optional)
├─ Dockerfile (optional)
└─ .env                               # Environment configuration
```

## Prerequisites

- Python 3.9+ (tested on 3.9–3.11)
- A virtual environment (Conda/venv)
- Node.js (only to serve the static frontend with `serve`)

## Quick Start

1) Create environment and install dependencies

```
# (Recommended) Use your Conda/venv environment
conda activate <your_env>

# From project root
pip install --upgrade pip
pip install -r requirements.txt
```

2) Configure environment

```
# Edit .env if needed
# Defaults are sensible for local runs
# Important entries
#   DATABASE_URL=sqlite:///railway_qr.db
#   JWT_SECRET_KEY=dev-jwt-secret
#   UPLOAD_FOLDER=uploads
#   QR_CODE_FOLDER=generated_qr_codes
```

3) Launch backend (Flask API)

```
# From project root
python backend/app.py
# Server starts at http://localhost:5000
```

4) Launch frontend (static server)

```
cd frontend
npx serve ./public -l 3000
# Open http://localhost:3000 in your browser
```

## Demo Login (Built-in Users)

- Manufacturer: `manufacturer / mfg123`
- Vendor: `vendor / vendor123`
- Railway Official: `official / rail123`

## Core Workflows

- Manufacturer dashboard
  - Fill item details (item_id, type, vendor lot, supply date, warranty)
  - Generate QR → PNG shown and available for download

- Vendor dashboard
  - Search parts (type, supplier, date range)
  - See UDM/TMS links for each item
  - Generate parts summary (JSON input) → returns summary and sync stubs

- Railway Official dashboard
  - Upload an image containing a QR code
  - Server-side pipeline decodes with confidence/quality metrics
  - If QR is recognized and present in DB, returns item details + AI insights

## API Endpoints (Summary)

- Auth
  - `POST /api/login` → { token, user }
  - `GET  /api/verify-token`

- Manufacturer
  - `POST /api/manufacturer/generate-qr` (JWT role=manufacturer)

- Vendor
  - `POST /api/vendor/search-parts` (JWT role=vendor)
  - `POST /api/vendor/parts-summary` (JWT role=vendor)

- Railway Official
  - `POST /api/official/scan-qr` (JWT role=railway_official) [multipart/form-data image]

- General
  - `GET /api/items`
  - `GET /api/download/qr/<qr_ref>`
  - `GET /api/health`

## AI Logic (Heuristics)

- Quality score:
  - Starts at 100; penalize if no recent inspections
- Maintenance prediction:
  - Based on item type and elapsed time since supply
- Risk assessment:
  - Elevated if long time without inspections or low quality score
- Recommendations:
  - Actionable text: schedule inspection, verify lot, etc.

> For production: replace with a trained model and store features/outputs in the DB.

## Hardware (Laser Marking)

- QR images (PNG) are suitable for laser engraving. For hardware integration:
  - Export vector (SVG) or keep high-res PNG
  - Add a small service/API to trigger engraver job submission with the item metadata

## Configuration Notes

- `.env` drives DB location and upload/QR folders
- Default DB: `sqlite:///railway_qr.db`
- UDM/TMS base URLs and API keys are configurable but optional for local demos

## Troubleshooting

- `ModuleNotFoundError: No module named 'flask_cors'`
  - Ensure you installed requirements in the active environment:
    - `pip install -r requirements.txt`
  - Confirm you are running Python in the same environment (e.g., `conda activate torch_gpu`)

- QR decoding issues on reflective/metal surfaces
  - Ensure clear, well-lit images; try different angles
  - The scanner already applies CLAHE/denoise/sharpen/threshold pipelines for better results

- Database not updating
  - Delete any old SQLite file (`railway_barcode.db`) and confirm `.env` points to `railway_qr.db`

## Roadmap / Enhancements

- Add live camera scanning in the Official dashboard with `html5-qrcode`
- Postgres migration + indices for scale
- PWA support for offline capture and deferred uploads
- Laser engraver integration API/driver
- Audit logs for scans + role traceability
- Unit/integration tests and CI

## License

This repository is for educational and prototyping purposes in the context of SIH 2025. Adjust the license as necessary for your deployment.
