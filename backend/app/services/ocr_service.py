import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pymupdf
import pytesseract
from PIL import Image

from backend.app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Manages image preprocessing and OCR extraction across PyMuPDF-embedded Tesseract
    and external Tesseract executable (via pytesseract).
    """

    def __init__(self):
        self._tessdata_dir = str(settings.tessdata_dir)
        os.environ["TESSDATA_PREFIX"] = self._tessdata_dir
        
        # Configure pytesseract command if available
        self._tesseract_available = False
        tess_cmd = settings.tesseract_cmd or shutil.which("tesseract")
        if not tess_cmd:
            # Check standard linux & windows binary locations
            common_paths = [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for p in common_paths:
                if os.path.exists(p):
                    tess_cmd = p
                    break

        if tess_cmd and os.path.exists(tess_cmd):
            pytesseract.pytesseract.tesseract_cmd = tess_cmd
            self._tesseract_available = True
            logger.info("Configured external Tesseract binary at %s", tess_cmd)
        else:
            logger.info("Using PyMuPDF native embedded Tesseract engine with tessdata: %s", self._tessdata_dir)

    @property
    def is_pytesseract_available(self) -> bool:
        return self._tesseract_available

    @property
    def is_ocr_available(self) -> bool:
        if self._tesseract_available:
            return True
        eng_file = Path(self._tessdata_dir) / "eng.traineddata"
        return eng_file.exists()

    @property
    def active_engine(self) -> Optional[str]:
        if self._tesseract_available:
            return "pytesseract"
        if (Path(self._tessdata_dir) / "eng.traineddata").exists():
            return "pymupdf_tesseract"
        return None

    def preprocess_image(self, img_bgr: np.ndarray) -> np.ndarray:
        """Applies image cleanup (grayscale, contrast normalization, thresholding)
        to improve OCR legibility on noisy or low-contrast scans.
        """
        if img_bgr is None or img_bgr.size == 0:
            return img_bgr

        # 1. Convert to grayscale
        if len(img_bgr.shape) == 3:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_bgr.copy()

        # 2. Rescale small images if DPI is low
        h, w = gray.shape[:2]
        if max(h, w) < 1000:
            scale_factor = 2.0
            gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

        # 3. Denoise with bilateral filter or Gaussian blur
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # 4. Otsu's adaptive thresholding for crisp text binarization
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Deskew if text has a noticeable orientation angle
        deskewed = self._deskew(thresh)
        return deskewed

    def _deskew(self, binary_img: np.ndarray) -> np.ndarray:
        """Estimates and corrects skew angle of the text image."""
        try:
            # Invert colors so text is foreground white
            inverted = cv2.bitwise_not(binary_img)
            coords = np.column_stack(np.where(inverted > 0))
            if len(coords) < 100:
                return binary_img

            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            # Only correct if skew is between 0.5 and 20 degrees
            if 0.5 < abs(angle) < 20.0:
                h, w = binary_img.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    binary_img,
                    M,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
                return rotated
        except Exception:
            pass
        return binary_img

    def ocr_image(self, img_bgr: np.ndarray, apply_preprocessing: bool = True) -> Dict[str, Any]:
        """Runs OCR on an image array.
        Returns extracted text, word bounding boxes, and word-level confidences.
        """
        if not self.is_ocr_available:
            raise RuntimeError(
                "OCR engine is not available. Please install Tesseract OCR or verify backend/app/tessdata/eng.traineddata exists."
            )

        processed_img = self.preprocess_image(img_bgr) if apply_preprocessing else img_bgr

        if self._tesseract_available:
            return self._ocr_with_pytesseract(processed_img)
        else:
            return self._ocr_with_pymupdf(processed_img)

    def _ocr_with_pytesseract(self, img: np.ndarray) -> Dict[str, Any]:
        """Runs pytesseract to get word-level coordinates and confidence metrics."""
        try:
            pil_img = Image.fromarray(img)
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            
            words = []
            full_text_list = []
            n_boxes = len(data["text"])
            
            for i in range(n_boxes):
                text = (data["text"][i] or "").strip()
                conf_val = float(data["conf"][i])
                if text:
                    # Tesseract confidence is 0-100; scale to 0.0-1.0
                    normalized_conf = max(0.0, min(1.0, conf_val / 100.0)) if conf_val >= 0 else None
                    words.append({
                        "word": text,
                        "confidence": normalized_conf,
                        "bbox": [
                            data["left"][i],
                            data["top"][i],
                            data["left"][i] + data["width"][i],
                            data["top"][i] + data["height"][i],
                        ],
                    })
                    full_text_list.append(text)
            
            combined_text = pytesseract.image_to_string(pil_img).strip()
            if not combined_text and full_text_list:
                combined_text = " ".join(full_text_list)

            return {
                "engine": "pytesseract",
                "text": combined_text,
                "words": words,
                "word_confidences": [w["confidence"] for w in words if w["confidence"] is not None],
            }
        except Exception as e:
            logger.warning("Pytesseract failed (%s), falling back to PyMuPDF native OCR", str(e))
            return self._ocr_with_pymupdf(img)

    def _ocr_with_pymupdf(self, img: np.ndarray) -> Dict[str, Any]:
        """Uses PyMuPDF's integrated native Tesseract engine."""
        # Encode image to PNG bytes
        success, encoded = cv2.imencode(".png", img)
        if not success:
            raise RuntimeError("Failed to encode preprocessed image for OCR.")
        
        png_bytes = encoded.tobytes()
        img_doc = pymupdf.open("png", png_bytes)
        try:
            pdf_bytes = img_doc.convert_to_pdf()
        finally:
            img_doc.close()

        pdf_doc = pymupdf.open("pdf", pdf_bytes)
        try:
            page = pdf_doc[0]
            tp = page.get_textpage_ocr(
                tessdata=self._tessdata_dir,
                language="eng",
                dpi=settings.ocr_dpi,
                full=True,
            )
            raw_words = tp.extractWORDS()
            extracted_text = tp.extractText().strip()
        finally:
            pdf_doc.close()

        words = []
        for w in raw_words:
            # Word coordinates and text
            word_str = w[4].strip()
            if word_str:
                words.append({
                    "word": word_str,
                    "confidence": 0.90,  # Base confidence for native OCR recognition
                    "bbox": [w[0], w[1], w[2], w[3]],
                })

        return {
            "engine": "pymupdf_tesseract",
            "text": extracted_text,
            "words": words,
            "word_confidences": [w["confidence"] for w in words],
        }

    def ocr_pdf_page(self, page: pymupdf.Page) -> Dict[str, Any]:
        """Renders a PDF page to a pixmap and runs OCR."""
        # Render page to high-res pixmap
        zoom = settings.ocr_dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert pixmap to numpy array
        img_arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))
        if pix.n == 4:
            img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2BGR)

        return self.ocr_image(img_bgr, apply_preprocessing=True)


ocr_service = OCRService()
