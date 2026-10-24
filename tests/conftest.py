import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of how pytest is invoked
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
import pymupdf
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    """Provides a managed FastAPI TestClient instance with lifespan lifecycle support."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_invoice_pdf_bytes():
    """Generates standard digital PDF invoice bytes with guaranteed resource cleanup."""
    with pymupdf.open() as doc:
        page = doc.new_page(width=595, height=842)
        text = """
Global Horizon Solutions LLC
990 Corporate Center, Suite 500
San Francisco, CA 94105

INVOICE

Invoice Number: INV-004821
Invoice Date: 2026-10-18
Due Date: 2026-11-18

Billed To:
Apex Industries Ltd
12 Enterprise Way

Description                         Qty    Rate        Amount
Enterprise Architecture Consulting    1    2500.00     2500.00

Financial Summary:
Subtotal: $2,500.00
Tax (10%): $250.00
Grand Total: $2,750.00

Thank you for your business.
"""
        page.insert_text((50, 80), text.strip(), fontsize=12)
        pdf_bytes = doc.tobytes()
    return pdf_bytes


@pytest.fixture
def sample_scanned_pdf_bytes():
    """Generates a scanned-style PDF where page has an embedded image instead of vector text."""
    # First generate text page and extract raster image bytes
    with pymupdf.open() as tmp_doc:
        p = tmp_doc.new_page(width=500, height=300)
        p.insert_text(
            (40, 50),
            "Scanned Vendor Corp\nInvoice #: SC-9912\nDate: 2026-09-12\nTotal: $450.00",
            fontsize=14,
        )
        pix = p.get_pixmap(dpi=150)
        png_bytes = pix.tobytes("png")

    # Place image in PDF via stream with explicit filetype
    with pymupdf.open(stream=png_bytes, filetype="png") as img_doc:
        pdf_bytes = img_doc.convert_to_pdf()
    return pdf_bytes


@pytest.fixture
def sample_invoice_png_bytes():
    """Generates a PNG image of an invoice with guaranteed resource cleanup."""
    with pymupdf.open() as doc:
        page = doc.new_page(width=500, height=350)
        text = """
Quantum Dynamics Ltd
100 Science Park

TAX INVOICE

Invoice No: QD-7740
Invoice Date: 2026-08-20

Item: Hardware Components
Subtotal: $1,200.00
Tax: $120.00
Grand Total: $1,320.00
"""
        page.insert_text((40, 60), text.strip(), fontsize=13)
        pix = page.get_pixmap(dpi=150)
        png_bytes = pix.tobytes("png")
    return png_bytes
