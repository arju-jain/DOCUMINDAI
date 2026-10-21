import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.schemas import DocumentProcessResponse
from backend.app.services.document_reader import DocumentReader, DocumentValidationError
from backend.app.services.field_extractor import FieldExtractor
from backend.app.services.ocr_service import ocr_service
from backend.app.services.validator import InvoiceValidator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])


@router.post(
    "/documents/process",
    response_model=DocumentProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process an uploaded document (PDF, PNG, JPG, JPEG)",
)
async def process_document(
    file: UploadFile = File(..., description="Uploaded invoice document (PDF, PNG, JPG, JPEG)"),
) -> DocumentProcessResponse:
    """Accepts a document upload, validates format and magic bytes, extracts text
    via digital parsing or OCR fallback, extracts invoice fields, and performs validation.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was provided in the upload request.",
        )

    document_id = str(uuid.uuid4())
    safe_filename = file.filename.replace("/", "_").replace("\\", "_")
    temp_path = None
    doc_ref = None

    try:
        # 1. Read file bytes
        content = await file.read()
        
        # 2. Validate file signature and size
        doc_category = DocumentReader.validate_file_signature(content, safe_filename)

        # 3. Save to safe temporary storage for processing
        ext = f".{doc_category}"
        temp_path = DocumentReader.save_temp_upload(content, suffix=ext)

        # 4. Extract Text and Words
        has_ocr = False
        words_meta = []
        raw_text = ""

        if doc_category == "pdf":
            parsed_doc = DocumentReader.read_pdf(content)
            doc_ref = parsed_doc.get("doc_ref")
            
            if parsed_doc["requires_ocr"]:
                # Embedded text insufficient -> execute OCR on pages
                has_ocr = True
                ocr_text_parts = []
                for page_idx in range(parsed_doc["processed_pages"]):
                    page = doc_ref[page_idx]
                    page_ocr_res = ocr_service.ocr_pdf_page(page)
                    ocr_text_parts.append(page_ocr_res["text"])
                    words_meta.extend(page_ocr_res.get("words", []))
                raw_text = "\n".join(ocr_text_parts).strip()
            else:
                raw_text = parsed_doc["raw_text"]
                has_ocr = False

        else:
            # Image (PNG, JPG, JPEG)
            img_data = DocumentReader.read_image(content)
            ocr_res = ocr_service.ocr_image(img_data["image_array"], apply_preprocessing=True)
            raw_text = ocr_res["text"]
            words_meta = ocr_res.get("words", [])
            has_ocr = True

        # 5. Extract Fields & Classify Document Type
        extractor = FieldExtractor(
            raw_text=raw_text,
            words_meta=words_meta,
            source_type=doc_category,
            has_ocr=has_ocr,
        )
        doc_type = extractor.classify_document_type()
        extracted_fields = extractor.extract_all()

        # 6. Validate Extracted Fields & Arithmetic
        validator = InvoiceValidator(fields=extracted_fields, raw_text=raw_text)
        validated_fields, validation_result = validator.validate()

        # 7. Build and Return Response Contract
        return DocumentProcessResponse(
            document_id=document_id,
            filename=safe_filename,
            document_type=doc_type,
            fields=validated_fields,
            validation=validation_result,
            metadata={
                "ocr_applied": has_ocr,
                "text_length": len(raw_text),
                "source_format": doc_category,
            },
        )

    except HTTPException as he:
        raise he
    except DocumentValidationError as dve:
        raise dve
    except Exception as exc:
        logger.exception("Unexpected error while processing document %s", safe_filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the document. Please verify the document format and try again.",
        )
    finally:
        # Guaranteed cleanup of resources and temporary file
        if doc_ref:
            try:
                doc_ref.close()
            except Exception:
                pass
        DocumentReader.safe_remove_temp(temp_path)
