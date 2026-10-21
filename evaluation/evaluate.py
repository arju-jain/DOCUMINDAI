import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.services.document_reader import DocumentReader
from backend.app.services.exporter import ReportExporter
from backend.app.services.field_extractor import FieldExtractor
from backend.app.services.ocr_service import ocr_service
from backend.app.services.validator import InvoiceValidator


def normalize_string(val: Optional[str]) -> str:
    """Normalizes string for comparison: trims whitespace and lowercases."""
    if not val:
        return ""
    return " ".join(val.strip().lower().split())


def compare_vendor(gt_val: Optional[str], pred_val: Optional[str]) -> bool:
    """Checks vendor name match via normalized equality or strong substring containment."""
    n_gt = normalize_string(gt_val)
    n_pred = normalize_string(pred_val)
    if not n_gt or not n_pred:
        return n_gt == n_pred
    return n_gt in n_pred or n_pred in n_gt


def compare_invoice_number(gt_val: Optional[str], pred_val: Optional[str]) -> bool:
    """Exact string match preserving leading zeros and symbols."""
    n_gt = (gt_val or "").strip().lower()
    n_pred = (pred_val or "").strip().lower()
    return n_gt == n_pred


def compare_date(gt_val: Optional[str], pred_val: Optional[str]) -> bool:
    """Exact ISO YYYY-MM-DD match."""
    n_gt = (gt_val or "").strip()
    n_pred = (pred_val or "").strip()
    return n_gt == n_pred


def compare_numeric(gt_val: Optional[float], pred_val: Optional[float], tolerance: float = 0.05) -> bool:
    """Compares monetary floats within rounding tolerance."""
    if gt_val is None and pred_val is None:
        return True
    if gt_val is None or pred_val is None:
        return False
    return abs(float(gt_val) - float(pred_val)) <= tolerance


def run_evaluation() -> Dict[str, Any]:
    """Executes the full evaluation pipeline across all held-out documents."""
    gt_file = settings.ground_truth_csv
    dataset_dir = settings.evaluation_dataset_dir

    if not gt_file.exists():
        raise FileNotFoundError(f"Ground truth file not found at: {gt_file}")
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found at: {dataset_dir}")

    # Read ground truth
    ground_truth_rows = []
    with open(gt_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ground_truth_rows = list(reader)

    total_docs = len(ground_truth_rows)
    if total_docs < 30:
        print(f"WARNING: Held-out dataset currently contains {total_docs} documents (< 30 required).")

    fields_to_eval = [
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "subtotal",
        "tax",
        "grand_total",
    ]

    field_stats = {
        f: {"evaluated": 0, "correct": 0, "missing": 0}
        for f in fields_to_eval
    }

    detailed_records = []
    success_count = 0
    fail_count = 0

    print(f"\n=======================================================")
    print(f"STARTING EVALUATION PIPELINE: {total_docs} HELD-OUT DOCUMENTS")
    print(f"=======================================================\n")

    for idx, row in enumerate(ground_truth_rows, start=1):
        doc_id = row["document_id"]
        filename = row["filename"]
        file_path = dataset_dir / filename

        if not file_path.exists():
            print(f"[{idx}/{total_docs}] FAILED: File {filename} not found.")
            fail_count += 1
            continue

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            doc_category = DocumentReader.validate_file_signature(content, filename)
            has_ocr = False
            words_meta = []
            raw_text = ""
            doc_ref = None

            if doc_category == "pdf":
                parsed_doc = DocumentReader.read_pdf(content)
                doc_ref = parsed_doc.get("doc_ref")
                if parsed_doc["requires_ocr"]:
                    has_ocr = True
                    ocr_parts = []
                    for p_i in range(parsed_doc["processed_pages"]):
                        p_res = ocr_service.ocr_pdf_page(doc_ref[p_i])
                        ocr_parts.append(p_res["text"])
                        words_meta.extend(p_res.get("words", []))
                    raw_text = "\n".join(ocr_parts).strip()
                else:
                    raw_text = parsed_doc["raw_text"]
                if doc_ref:
                    doc_ref.close()
            else:
                img_data = DocumentReader.read_image(content)
                ocr_res = ocr_service.ocr_image(img_data["image_array"], apply_preprocessing=True)
                raw_text = ocr_res["text"]
                words_meta = ocr_res.get("words", [])
                has_ocr = True

            # Extract fields
            extractor = FieldExtractor(
                raw_text=raw_text,
                words_meta=words_meta,
                source_type=doc_category,
                has_ocr=has_ocr,
            )
            extracted = extractor.extract_all()
            doc_type = extractor.classify_document_type()

            # Validate fields
            validator = InvoiceValidator(fields=extracted, raw_text=raw_text)
            validated_fields, val_result = validator.validate()

            success_count += 1

            # Field comparisons
            # 1. Vendor
            gt_v = row.get("vendor_name")
            pred_v = validated_fields.vendor_name.value
            v_match = compare_vendor(gt_v, pred_v)

            # 2. Invoice Number
            gt_num = row.get("invoice_number")
            pred_num = validated_fields.invoice_number.value
            num_match = compare_invoice_number(gt_num, pred_num)

            # 3. Invoice Date
            gt_d = row.get("invoice_date")
            pred_d = validated_fields.invoice_date.value
            d_match = compare_date(gt_d, pred_d)

            # 4. Subtotal
            gt_st = float(row["subtotal"]) if row.get("subtotal") else None
            pred_st = validated_fields.subtotal.value
            st_match = compare_numeric(gt_st, pred_st)

            # 5. Tax
            gt_tx = float(row["tax"]) if row.get("tax") else None
            pred_tx = validated_fields.tax.value
            tx_match = compare_numeric(gt_tx, pred_tx)

            # 6. Grand Total
            gt_gt = float(row["grand_total"]) if row.get("grand_total") else None
            pred_gt = validated_fields.grand_total.value
            gt_match = compare_numeric(gt_gt, pred_gt)

            # Update stats
            matches_map = {
                "vendor_name": (gt_v, pred_v, v_match),
                "invoice_number": (gt_num, pred_num, num_match),
                "invoice_date": (gt_d, pred_d, d_match),
                "subtotal": (gt_st, pred_st, st_match),
                "tax": (gt_tx, pred_tx, tx_match),
                "grand_total": (gt_gt, pred_gt, gt_match),
            }

            for f_name, (gt_val, pred_val, is_match) in matches_map.items():
                if gt_val is not None:
                    field_stats[f_name]["evaluated"] += 1
                    if pred_val is None:
                        field_stats[f_name]["missing"] += 1
                    elif is_match:
                        field_stats[f_name]["correct"] += 1

            record = {
                "document_id": doc_id,
                "filename": filename,
                "document_type": doc_type,
                "status": "processed",
                "vendor_name_gt": gt_v,
                "vendor_name_pred": pred_v,
                "vendor_name_match": v_match,
                "invoice_number_gt": gt_num,
                "invoice_number_pred": pred_num,
                "invoice_number_match": num_match,
                "invoice_date_gt": gt_d,
                "invoice_date_pred": pred_d,
                "invoice_date_match": d_match,
                "subtotal_gt": gt_st,
                "subtotal_pred": pred_st,
                "subtotal_match": st_match,
                "tax_gt": gt_tx,
                "tax_pred": pred_tx,
                "tax_match": tx_match,
                "grand_total_gt": gt_gt,
                "grand_total_pred": pred_gt,
                "grand_total_match": gt_match,
                "overall_valid": val_result.overall_status == "valid",
            }
            detailed_records.append(record)

            all_matched = v_match and num_match and d_match and st_match and tx_match and gt_match
            print(f"[{idx:02d}/{total_docs}] {filename} -> {'PASS' if all_matched else 'PARTIAL'}")

        except Exception as e:
            fail_count += 1
            print(f"[{idx:02d}/{total_docs}] {filename} -> ERROR: {str(e)}")
            detailed_records.append({
                "document_id": doc_id,
                "filename": filename,
                "document_type": "unknown",
                "status": "failed",
                "vendor_name_match": False,
                "invoice_number_match": False,
                "invoice_date_match": False,
                "subtotal_match": False,
                "tax_match": False,
                "grand_total_match": False,
                "overall_valid": False,
            })

    # Compile Final Report
    field_metrics = {}
    total_correct_across_all = 0
    total_evaluated_across_all = 0

    for f_name, stats in field_stats.items():
        eval_count = stats["evaluated"]
        corr_count = stats["correct"]
        miss_count = stats["missing"]
        acc = round((corr_count / eval_count * 100.0), 2) if eval_count > 0 else 0.0

        field_metrics[f_name] = {
            "evaluated_count": eval_count,
            "correct_count": corr_count,
            "missing_count": miss_count,
            "accuracy_percentage": acc,
        }
        total_correct_across_all += corr_count
        total_evaluated_across_all += eval_count

    overall_accuracy = (
        round((total_correct_across_all / total_evaluated_across_all * 100.0), 2)
        if total_evaluated_across_all > 0
        else 0.0
    )

    report_payload = {
        "status": "completed",
        "total_documents": total_docs,
        "successfully_processed": success_count,
        "failed_processing": fail_count,
        "field_metrics": field_metrics,
        "overall_accuracy_percentage": overall_accuracy,
        "normalization_rules": {
            "dates": "Normalized to ISO YYYY-MM-DD when unambiguous (e.g. named months, Day > 12); rejected if ambiguous.",
            "monetary": "Parsed to standard numeric float rounded to 2 decimal places with $0.05 rounding tolerance.",
            "invoice_numbers": "Preserved as exact strings including leading zeros.",
            "vendors": "Normalized by stripping excess whitespace and comparing normalized substring/equality.",
        },
        "evaluated_at": datetime.now().isoformat(),
    }

    # Save to JSON and CSV
    json_path, csv_path = ReportExporter.save_evaluation_report(report_payload, detailed_records)
    print(f"\n=======================================================")
    print(f"EVALUATION SUMMARY:")
    print(f"Total Documents: {total_docs}")
    print(f"Successfully Processed: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Overall Field Accuracy: {overall_accuracy}%")
    print(f"\nField-by-Field Accuracy:")
    for f_name, met in field_metrics.items():
        print(f"  - {f_name:15s}: {met['accuracy_percentage']:6.2f}% ({met['correct_count']}/{met['evaluated_count']}) | Missing: {met['missing_count']}")
    print(f"\nReports saved to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    print(f"=======================================================\n")

    return report_payload


if __name__ == "__main__":
    run_evaluation()
