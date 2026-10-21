import os
import pytest
from fastapi import HTTPException

from backend.app.services.document_reader import DocumentReader, DocumentValidationError


def test_validate_pdf_signature():
    pdf_bytes = b"%PDF-1.7\n%some content"
    assert DocumentReader.validate_file_signature(pdf_bytes, "invoice.pdf") == "pdf"


def test_validate_png_signature():
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    assert DocumentReader.validate_file_signature(png_bytes, "scan.png") == "png"


def test_validate_jpeg_signature():
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    assert DocumentReader.validate_file_signature(jpeg_bytes, "receipt.jpg") == "jpeg"
    assert DocumentReader.validate_file_signature(jpeg_bytes, "receipt.jpeg") == "jpeg"


def test_reject_empty_file():
    with pytest.raises(DocumentValidationError) as exc:
        DocumentReader.validate_file_signature(b"", "empty.pdf")
    assert exc.value.status_code == 400
    assert "empty" in str(exc.value.detail).lower()


def test_reject_unsupported_extension():
    with pytest.raises(DocumentValidationError) as exc:
        DocumentReader.validate_file_signature(b"%PDF-1.4", "document.docx")
    assert exc.value.status_code == 415


def test_reject_invalid_signature():
    with pytest.raises(DocumentValidationError) as exc:
        DocumentReader.validate_file_signature(b"Plain text content", "fake.pdf")
    assert exc.value.status_code == 415


def test_text_sufficiency_heuristic():
    # Long clear text
    long_text = "This is a legitimate digital invoice document with comprehensive description lines and sufficient characters."
    assert DocumentReader.is_text_sufficient(long_text) is True

    # Empty or short text
    assert DocumentReader.is_text_sufficient("") is False
    assert DocumentReader.is_text_sufficient("    \n\n   ") is False
    assert DocumentReader.is_text_sufficient("Page 1") is False


def test_safe_temp_file_lifecycle():
    data = b"sample temporary data for processing"
    temp_path = DocumentReader.save_temp_upload(data, suffix=".pdf")
    assert os.path.exists(temp_path)
    with open(temp_path, "rb") as f:
        assert f.read() == data

    # Cleanup
    DocumentReader.safe_remove_temp(temp_path)
    assert not os.path.exists(temp_path)


def test_corrupt_pdf_handling():
    corrupted_bytes = b"%PDF-corruptedgarbage12345"
    with pytest.raises(DocumentValidationError) as exc:
        DocumentReader.inspect_pdf(corrupted_bytes)
    assert exc.value.status_code == 422


def test_encrypted_pdf_handling():
    import pymupdf
    doc = pymupdf.open()
    p = doc.new_page(width=300, height=100)
    p.insert_text((20, 20), "Secret content")
    enc_bytes = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="secret", user_pw="secret")
    doc.close()

    with pytest.raises(DocumentValidationError) as exc:
        DocumentReader.inspect_pdf(enc_bytes)
    assert exc.value.status_code == 422
    assert "encrypted" in str(exc.value.detail).lower()
