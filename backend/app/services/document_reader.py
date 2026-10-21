import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import cv2
import numpy as np
import pymupdf
from fastapi import HTTPException, status

from backend.app.config import settings


class DocumentValidationError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class DocumentReader:
    """Safely validates, parses, and extracts raw text or renders pages from uploaded documents."""

    @staticmethod
    def validate_file_signature(content: bytes, original_filename: str) -> str:
        """Validates file magic numbers and basic structural integrity.
        Returns the normalized document category ('pdf' or 'image').
        """
        if not content or len(content) == 0:
            raise DocumentValidationError("The uploaded file is empty.", status_code=status.HTTP_400_BAD_REQUEST)

        if len(content) > settings.max_upload_size_bytes:
            max_mb = settings.max_upload_size_bytes / (1024 * 1024)
            raise DocumentValidationError(
                f"File size exceeds the allowed limit of {max_mb:.1f} MB.",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Sanitize extension check
        ext = Path(original_filename).suffix.lower()
        if ext not in settings.allowed_extensions:
            raise DocumentValidationError(
                f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(settings.allowed_extensions)}",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # Check magic bytes
        if content[:4] == b"%PDF" or b"%PDF-" in content[:1024]:
            return "pdf"
        elif content.startswith(settings.magic_signatures["png"]):
            return "png"
        elif content.startswith(settings.magic_signatures["jpeg"]):
            return "jpeg"
        else:
            raise DocumentValidationError(
                "File signature does not match any accepted formats (PDF, PNG, JPG, JPEG).",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

    @staticmethod
    def inspect_pdf(content: bytes) -> Tuple[pymupdf.Document, int]:
        """Safely opens a PDF from bytes, verifies it is uncorrupted, unencrypted, and within page limits."""
        try:
            doc = pymupdf.open(stream=content, filetype="pdf")
        except Exception as e:
            raise DocumentValidationError(
                f"Failed to parse PDF document: Corrupted or unreadable format.",
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        if doc.is_encrypted or doc.needs_pass:
            doc.close()
            raise DocumentValidationError(
                "Encrypted or password-protected PDFs are not supported.",
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise DocumentValidationError(
                "The PDF document contains no pages.",
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        return doc, page_count

    @staticmethod
    def is_text_sufficient(text: str) -> bool:
        """Determines whether extracted embedded text is sufficient or if OCR fallback is needed.
        Scanned PDFs typically yield empty strings, random whitespace, or very few characters.
        """
        cleaned = re.sub(r"\s+", "", text)
        if len(cleaned) < 50:
            return False

        # Check word density
        words = text.split()
        if len(words) < 10:
            return False

        # Check printable character ratio to avoid binary/corrupted font garbage
        printable = sum(1 for c in text if c.isprintable() or c in "\r\n\t")
        if (printable / len(text)) < 0.85:
            return False

        return True

    @staticmethod
    def read_pdf(content: bytes) -> Dict[str, Any]:
        """Extracts text from PDF, deciding whether embedded text is sufficient or OCR is required."""
        doc, page_count = DocumentReader.inspect_pdf(content)
        pages_to_process = min(page_count, settings.max_pages)
        
        extracted_pages = []
        full_text_parts = []
        requires_ocr = False
        
        try:
            for page_idx in range(pages_to_process):
                page = doc[page_idx]
                page_text = page.get_text("text") or ""
                
                # Check sufficiency of embedded text on this page
                if not DocumentReader.is_text_sufficient(page_text):
                    requires_ocr = True
                
                extracted_pages.append({
                    "page_number": page_idx + 1,
                    "text": page_text,
                    "rect": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
                })
                full_text_parts.append(page_text)
            
            combined_text = "\n".join(full_text_parts).strip()
            
            # If the entire combined text is insufficient, we definitely need OCR
            if not DocumentReader.is_text_sufficient(combined_text):
                requires_ocr = True

            return {
                "source_type": "pdf",
                "page_count": page_count,
                "processed_pages": pages_to_process,
                "requires_ocr": requires_ocr,
                "raw_text": combined_text,
                "pages": extracted_pages,
                "doc_ref": doc,  # Pass doc along for rendering if OCR is required
            }
        except Exception as e:
            doc.close()
            if isinstance(e, DocumentValidationError):
                raise e
            raise DocumentValidationError(
                f"Error extracting content from PDF: {str(e)}",
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

    @staticmethod
    def read_image(content: bytes) -> Dict[str, Any]:
        """Safely decodes an uploaded image and validates its integrity."""
        np_arr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None or img.size == 0:
            raise DocumentValidationError(
                "Uploaded image is corrupted or cannot be decoded.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        h, w = img.shape[:2]
        return {
            "source_type": "image",
            "page_count": 1,
            "processed_pages": 1,
            "requires_ocr": True,
            "image_array": img,
            "width": w,
            "height": h,
            "raw_bytes": content,
        }

    @staticmethod
    def save_temp_upload(content: bytes, suffix: str = ".tmp") -> str:
        """Saves content to a secure, randomly named temporary file and returns its path."""
        unique_name = f"doc_{uuid.uuid4().hex}{suffix}"
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, unique_name)
        with open(temp_path, "wb") as f:
            f.write(content)
        return temp_path

    @staticmethod
    def safe_remove_temp(temp_path: Optional[str]) -> None:
        """Safely cleans up temporary file without throwing errors."""
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
