import csv
import io
import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Response, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Export"])


@router.post(
    "/export/csv",
    summary="Export extracted document data as RFC-4180 CSV",
    response_description="CSV file attachment",
)
def export_csv(payload: Dict[str, Any]):
    """Accepts document extraction results and returns a properly formatted RFC-4180 CSV file."""
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must not be empty.",
        )

    doc_id = payload.get("document_id") or "documind_document"
    doc_type = payload.get("document_type") or "invoice"
    fields = payload.get("fields") or {}

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")

    # CSV Header
    writer.writerow([
        "document_id",
        "document_type",
        "field_name",
        "value",
        "confidence",
        "status",
        "validation_message",
    ])

    for key, f in fields.items():
        if isinstance(f, dict):
            val = f.get("value")
            val_str = str(val) if val is not None else ""
            conf = f.get("confidence")
            conf_str = f"{round(conf * 100)}%" if isinstance(conf, (int, float)) else "Unavailable"
            st = f.get("status") or ("missing" if val is None else "extracted")
            msg = f.get("validation_message") or ""
        else:
            val_str = str(f) if f is not None else ""
            conf_str = "Unavailable"
            st = "missing" if not val_str else "extracted"
            msg = ""

        writer.writerow([doc_id, doc_type, key, val_str, conf_str, st, msg])

    csv_content = "\ufeff" + output.getvalue()  # UTF-8 BOM for Excel compatibility
    filename = f"documind_export_{doc_id}.csv"

    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/export/json",
    summary="Export extracted document data as formatted JSON",
    response_description="JSON file attachment",
)
def export_json(payload: Dict[str, Any]):
    """Accepts document extraction results and returns formatted JSON."""
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must not be empty.",
        )

    doc_id = payload.get("document_id") or "documind_document"
    formatted_json = json.dumps(payload, indent=2, ensure_ascii=False)
    filename = f"documind_export_{doc_id}.json"

    return Response(
        content=formatted_json.encode("utf-8"),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
