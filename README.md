# DocuMind AI — Multimodal Document Intelligence

> **Unified Full-Stack System**: Automated high-precision invoice & document understanding pipeline with an interactive SaaS frontend and FastAPI REST backend.

---

## 1. Unified Project Architecture

```
multidocument/
├── backend/                       # Production FastAPI REST Backend
│   ├── app/
│   │   ├── config.py             # Settings, limits, CORS origins, and paths
│   │   ├── main.py               # FastAPI application entrypoint & middleware
│   │   ├── models/               # Pydantic v2 domain schemas & contracts
│   │   │   └── document.py
│   │   ├── routes/               # API route definitions
│   │   │   ├── __init__.py
│   │   │   ├── documents.py      # POST /api/documents/process
│   │   │   ├── evaluation.py     # GET /api/evaluation
│   │   │   ├── export.py         # POST /api/export/csv, /api/export/json
│   │   │   └── health.py         # GET /api/health
│   │   ├── services/             # Core business & extraction services
│   │   │   ├── confidence.py     # 70% OCR + 30% syntactic calibration
│   │   │   ├── document_reader.py# File validation, magic bytes & multi-page safety
│   │   │   ├── exporter.py       # RFC-4180 CSV & JSON serialization
│   │   │   ├── field_extractor.py# Multi-currency, multi-format invoice extractor
│   │   │   ├── ocr_service.py    # PyMuPDF Tesseract engine & OpenCV binarizer
│   │   │   └── validator.py      # Arithmetic, date, and discount/charge validation
│   │   └── tessdata/             # Bundled eng.traineddata OCR model
│   └── __init__.py
├── frontend/                      # Modern Vanilla SaaS Frontend Client
│   ├── index.html                # Semantic UI dashboard, tables, validation panels
│   ├── style.css                 # Responsive stylesheet, status badges & edit controls
│   ├── script.js                 # Modular ES6+ client (API, state, manual edit, filters)
│   └── assets/                   # Brand logo & sample invoice assets
│       ├── logo.svg
│       ├── sample_invoice.pdf
│       ├── sample_invoice.png
│       └── sample_invoice.svg
├── tests/                         # Pytest test suite (49 automated tests)
│   ├── conftest.py
│   ├── test_api_endpoints.py
│   ├── test_document_reader.py
│   ├── test_evaluation_pipeline.py
│   ├── test_field_extractor.py
│   ├── test_ocr_service.py
│   └── test_validator.py
├── evaluation/                    # Held-Out Benchmark Evaluation Suite
│   ├── dataset/                  # 32 benchmark documents (24 PDFs, 8 Images)
│   ├── ground_truth.csv          # Human-verified ground truth annotations
│   └── evaluate.py               # Evaluation benchmark pipeline runner
├── reports/                       # Generated evaluation outputs
│   ├── evaluation_report.csv
│   └── evaluation_report.json
├── index.html                     # Root redirect helper to frontend/
├── start_dev.ps1                  # Optional full-stack starter convenience script
├── Dockerfile                     # Multi-stage production container definition
├── docker-compose.yml             # Local & production container orchestration
├── .dockerignore                  # Docker build exclusions
├── requirements.txt               # Backend Python dependencies
├── .env.example                   # Safe template for environment variables
├── .env                           # Local environment configuration (never committed)
├── .gitignore                     # Git ignore rules for venv, secrets, logs, uploads
└── README.md                      # Unified project guide & technical documentation
```

---

## 2. Quick Start: Running the Project

From the project root directory (`C:\Users\arjun\OneDrive\Desktop\multidocument`):

### Terminal 1: Start the Backend Server (Port 8000)

```powershell
.\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Backend Base URL**: `http://127.0.0.1:8000`
- **Health Check**: `http://127.0.0.1:8000/api/health`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Schema**: `http://127.0.0.1:8000/redoc`

### Terminal 2: Start the Frontend Client (Port 8081)

```powershell
python -m http.server 8081 --bind 127.0.0.1 --directory frontend
```

- **Frontend Application**: `http://127.0.0.1:8081/`

*(Optional Convenience)*: You can also run `.\start_dev.ps1` in PowerShell to launch both services in dedicated console windows with live logs.

---

## 3. Frontend & Backend Integration

The frontend client communicates with the FastAPI backend over REST:

- **Configured Base URL**: `http://127.0.0.1:8000/api`
- **Document Processing**: `POST /api/documents/process`
  - Uploaded as `multipart/form-data` with field name `file`.
  - Browser automatically supplies multipart boundaries (no manual Content-Type header).
- **Health Check**: `GET /api/health`
- **Evaluation Benchmark**: `GET /api/evaluation`

### CORS Security Configuration
The backend strictly restricts CORS to designated local development frontend origins in `backend/app/config.py` and `.env`:
```ini
CORS_ORIGINS=http://127.0.0.1:8081,http://localhost:8081,http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:5500,http://localhost:5500,http://localhost:5173,http://localhost:3000
```
Unrestricted wildcards (`*`) are disabled to ensure safe origin isolation.

---

## 4. Key Extraction & Validation Features

1. **No Field Fabrication**: If a field is not present in the document, `value: null`, `confidence: null`, and `status: "missing"` are returned. The system never invents missing invoice numbers, dates, or amounts.
2. **Absent vs. OCR Failure Distinction**:
   - *Absent Field*: Label not present in layout &rarr; `status: "missing"`, displayed with a neutral slate dashed badge.
   - *OCR Recognition Failure*: Label detected (e.g. `Tax:`) but followed by blank or unparseable characters &rarr; `status: "needs_review"`, `confidence: 0.20`, displayed as `Unparseable / OCR Failure`.
3. **Safe Arithmetic Validation**:
   - Arithmetic verification (`subtotal + tax ≈ grand_total`) runs **only when numeric values are available**.
   - The system **never assumes tax is zero** when tax is absent, and **never assumes subtotal equals grand total**.
   - If an invoice contains discounts or charges (shipping, freight, handling, fees), arithmetic discrepancies are marked as `TOTAL_MISMATCH_WITH_ADJUSTMENTS` (`needs_review`) rather than hard errors.
4. **Broad Layout & Multi-Currency Support**:
   - Supports `$`, `€`, `£`, `₹`, `¥`, `USD`, `EUR`, `GBP`, `INR`, `CAD`, `AUD`.
   - Supports both US numbers (`1,250.00`) and European numbers (`1.250,00`).
   - Supports single-line, colon-delimited, and stacked (multi-line) label-value pairs.
5. **Interactive Frontend Correction & Filtering**:
   - Inline **Edit** / **Add** buttons allow instant manual entry of absent or corrected fields.
   - Manual edits dynamically recalculate totals and resolve validation warnings in real-time.
   - Quick filters (`All`, `Review`, `Missing`, `Invalid`) alongside live text search.

---

## 5. Testing & Verification

### Run Automated Unit & Integration Tests (55 Tests)
```powershell
.\venv\Scripts\python -m pytest -v
```
*Current test suite: **55 passed, 0 failed, 0 warnings**.*

### Run Benchmark Accuracy Evaluation (32 Held-Out Documents)
```powershell
.\venv\Scripts\python evaluation/evaluate.py
```
*Current benchmark accuracy: **100.0%** across all 32 held-out invoices.*

### Verify Frontend JavaScript Syntax
```powershell
node --check frontend/script.js
```

---

## 6. Docker & Production Deployment Guide

DocuMind AI provides a production-hardened containerization setup with multi-worker ASGI execution and automated health monitoring. In container environments, the backend also serves the static frontend dashboard at `/` so that the entire solution can be deployed as a single turnkey service.

### Quick Start with Docker Compose

```bash
# Build and launch the container in the background
docker-compose up -d --build

# Verify container health
docker-compose ps
```

- **Unified Dashboard & API**: `http://localhost:8000/`
- **REST API Endpoint**: `http://localhost:8000/api`
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`
- **Container Health Check**: `http://localhost:8000/api/health`

### Building and Running with Standalone Docker

```bash
# Build production Docker image
docker build -t documind-ai:latest .

# Run the container
docker run -d \
  --name documind-app \
  -p 8000:8000 \
  -e CORS_ORIGINS="http://localhost:8000,http://127.0.0.1:8000" \
  -e SERVE_FRONTEND=True \
  --restart unless-stopped \
  documind-ai:latest
```

### Production Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `HOST` | `0.0.0.0` | Network binding interface for the ASGI server |
| `PORT` | `8000` | Port on which the ASGI server listens |
| `DEBUG` | `False` | Disables debug mode and autoreload in production |
| `SERVE_FRONTEND` | `True` | Serves the frontend web dashboard from `/` |
| `CORS_ORIGINS` | *(Local dev origins)* | Comma-separated whitelist of allowed browser origins |
| `MAX_UPLOAD_SIZE_BYTES` | `15728640` (15 MB) | Maximum permitted file upload size in bytes |
| `MAX_PAGES` | `15` | Maximum PDF pages processed per document |
| `TESSERACT_CMD` | `""` (auto-detect) | Absolute path to external Tesseract executable if custom |
| `TESSDATA_DIR` | `backend/app/tessdata` | Path to directory containing `eng.traineddata` |
| `OCR_DPI` | `150` | DPI resolution used for PDF page rasterization |
| `CONFIDENCE_THRESHOLD` | `0.60` | Score threshold below which fields are marked `low_confidence` |
| `ROUNDING_TOLERANCE` | `0.05` | Currency arithmetic tolerance for validation |

### System OCR Engine Setup

The application features a dual-layer OCR architecture:
1. **PyMuPDF Embedded Tesseract (Built-in)**: Uses `backend/app/tessdata/eng.traineddata` to run native C++ OCR without requiring external binaries.
2. **System Tesseract (Container / Server)**: The provided `Dockerfile` installs `tesseract-ocr` and `tesseract-ocr-eng` via Debian APT for maximum throughput and compatibility.
   - On Debian / Ubuntu: `sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libgl1`
   - On Windows: Download and install from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) to `C:\Program Files\Tesseract-OCR\tesseract.exe`.

