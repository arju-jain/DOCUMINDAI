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

### Run Automated Unit & Integration Tests (49 Tests)
```powershell
$env:PYTHONPATH='.'; .\venv\Scripts\python -m pytest -v
```

### Run Benchmark Accuracy Evaluation (32 Held-Out Documents)
```powershell
.\venv\Scripts\python evaluation/evaluate.py
```
*Current benchmark accuracy: **100.0%** across all 32 held-out invoices.*

### Verify Frontend JavaScript Syntax
```powershell
node --check frontend/script.js
```
