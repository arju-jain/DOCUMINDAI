import numpy as np
import pytest
from backend.app.services.ocr_service import ocr_service


def test_preprocess_image_dimensions():
    # Create synthetic test image
    img = np.full((100, 300, 3), 255, dtype=np.uint8)
    processed = ocr_service.preprocess_image(img)
    assert processed is not None
    assert len(processed.shape) == 2  # Binarized grayscale single-channel


def test_deskew_no_crash_on_blank():
    blank = np.zeros((200, 200), dtype=np.uint8)
    deskewed = ocr_service._deskew(blank)
    assert deskewed.shape == blank.shape


def test_ocr_image_execution(sample_invoice_png_bytes):
    import cv2
    np_arr = np.frombuffer(sample_invoice_png_bytes, np.uint8)
    img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    assert img_bgr is not None

    result = ocr_service.ocr_image(img_bgr)
    assert "text" in result
    assert "words" in result
    assert len(result["text"]) > 0
    # Check that keywords from the fixture are present in OCR output
    extracted_lower = result["text"].lower()
    assert "quantum" in extracted_lower or "invoice" in extracted_lower
