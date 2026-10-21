import pytest
import pymupdf
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    """Provides a FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def sample_invoice_pdf_bytes():
    """Generates standard digital PDF invoice bytes."""
    doc = pymupdf.open()
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
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_scanned_pdf_bytes():
    """Generates a scanned-style PDF where page has an embedded image instead of vector text."""
    # First generate text page
    tmp_doc = pymupdf.open()
    p = tmp_doc.new_page(width=500, height=300)
    p.insert_text((40, 50), "Scanned Vendor Corp\nInvoice #: SC-9912\nDate: 2026-09-12\nTotal: $450.00", fontsize=14)
    pix = p.get_pixmap(dpi=150)
    png_bytes = pix.tobytes()
    tmp_doc.close()

    # Place image in PDF
    img_doc = pymupdf.open("png", png_bytes)
    pdf_bytes = img_doc.convert_to_pdf()
    img_doc.close()
    return pdf_bytes


@pytest.fixture
def sample_invoice_png_bytes():
    """Generates a PNG image of an invoice."""
    doc = pymupdf.open()
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
    png_bytes = pix.tobytes()
    doc.close()
    return png_bytes
