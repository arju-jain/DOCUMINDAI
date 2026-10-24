import pymupdf
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "ocr_available" in data


def test_process_document_success(client: TestClient, sample_invoice_pdf_bytes):
    response = client.post(
        "/api/documents/process",
        files={"file": ("invoice.pdf", sample_invoice_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "invoice.pdf"
    assert data["document_type"] == "invoice"

    # Contract validation: all 6 fields exist
    fields = data["fields"]
    for required_field in [
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "subtotal",
        "tax",
        "grand_total",
    ]:
        assert required_field in fields
        assert "value" in fields[required_field]
        assert "confidence" in fields[required_field]
        assert "status" in fields[required_field]

    assert fields["invoice_number"]["value"] == "INV-004821"
    assert fields["subtotal"]["value"] == 2500.00
    assert fields["tax"]["value"] == 250.00
    assert fields["grand_total"]["value"] == 2750.00
    assert data["validation"]["overall_status"] == "valid"


def test_process_image_document(client: TestClient, sample_invoice_png_bytes):
    response = client.post(
        "/api/documents/process",
        files={"file": ("scan.png", sample_invoice_png_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["ocr_applied"] is True
    assert data["document_type"] == "invoice"


def test_process_empty_file_rejected(client: TestClient):
    response = client.post(
        "/api/documents/process",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_process_unsupported_file_rejected(client: TestClient):
    response = client.post(
        "/api/documents/process",
        files={"file": ("script.py", b"print('hello')", "text/plain")},
    )
    assert response.status_code == 415


def test_process_corrupt_pdf_rejected(client: TestClient):
    response = client.post(
        "/api/documents/process",
        files={"file": ("corrupt.pdf", b"%PDF-1.4 garbage corruption", "application/pdf")},
    )
    assert response.status_code == 422


def test_evaluation_endpoint(client: TestClient):
    response = client.get("/api/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("completed", "unavailable")
    if data["status"] == "completed":
        assert "field_metrics" in data
        assert "overall_accuracy_percentage" in data


def test_process_document_with_missing_tax(client: TestClient):
    with pymupdf.open() as doc:
        page = doc.new_page(width=500, height=400)
        text = """
Nexus Global Partners
100 First Street

INVOICE
Invoice No: NX-1002
Date: 2026-10-19

Subtotal: $500.00
Total: $500.00
"""
        page.insert_text((40, 50), text.strip(), fontsize=12)
        pdf_bytes = doc.tobytes()

    response = client.post(
        "/api/documents/process",
        files={"file": ("no_tax_invoice.pdf", pdf_bytes, "application/pdf")},
    )
    # Does not fail the entire document merely because tax is missing
    assert response.status_code == 200
    data = response.json()
    assert data["fields"]["tax"]["value"] is None
    assert data["fields"]["tax"]["status"] == "missing"
    assert data["fields"]["subtotal"]["value"] == 500.00
    assert data["fields"]["grand_total"]["value"] == 500.00
    assert data["fields"]["invoice_number"]["value"] == "NX-1002"
    # Returns all extracted fields and validation results
    assert "validation" in data


def test_export_csv_endpoint(client: TestClient):
    payload = {
        "document_id": "INV-TEST-001",
        "document_type": "invoice",
        "fields": {
            "vendor_name": {"value": "TechCorp", "confidence": 0.95, "status": "extracted"},
            "grand_total": {"value": 1500.0, "confidence": 0.99, "status": "extracted"},
        },
    }
    response = client.post("/api/export/csv", json=payload)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=\"documind_export_INV-TEST-001.csv\"" in response.headers["content-disposition"]
    text = response.text
    assert "vendor_name" in text
    assert "TechCorp" in text
    assert "grand_total" in text


def test_export_json_endpoint(client: TestClient):
    payload = {
        "document_id": "INV-TEST-002",
        "document_type": "invoice",
        "fields": {
            "vendor_name": {"value": "TechCorp", "confidence": 0.95, "status": "extracted"},
        },
    }
    response = client.post("/api/export/json", json=payload)
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "attachment; filename=\"documind_export_INV-TEST-002.json\"" in response.headers["content-disposition"]
    data = response.json()
    assert data["document_id"] == "INV-TEST-002"
    assert data["fields"]["vendor_name"]["value"] == "TechCorp"


def test_export_empty_payload_rejected(client: TestClient):
    response = client.post("/api/export/csv", json={})
    assert response.status_code == 400


def test_process_oversized_file_rejected(client: TestClient):
    # Create oversized content larger than 15MB
    large_pdf_header = b"%PDF-1.4\n" + b"A" * (16 * 1024 * 1024)
    response = client.post(
        "/api/documents/process",
        files={"file": ("large_invoice.pdf", large_pdf_header, "application/pdf")},
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()


def test_api_info_endpoint(client: TestClient):
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "documentation" in data
    assert "health_check" in data


def test_root_serves_frontend(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "DocuMind" in response.text or "<!DOCTYPE html>" in response.text
