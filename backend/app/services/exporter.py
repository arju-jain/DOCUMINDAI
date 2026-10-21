import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.config import settings


class ReportExporter:
    """Manages exporting and loading evaluation reports in both JSON and CSV formats."""

    @staticmethod
    def save_evaluation_report(
        report_data: Dict[str, Any],
        detailed_records: Optional[List[Dict[str, Any]]] = None,
        json_path: Optional[Path] = None,
        csv_path: Optional[Path] = None,
    ) -> Tuple[Path, Path]:
        """Saves evaluation metrics to JSON and detailed per-document comparisons to CSV."""
        target_json = json_path or settings.evaluation_report_json
        target_csv = csv_path or settings.evaluation_report_csv

        # Ensure directory exists
        target_json.parent.mkdir(parents=True, exist_ok=True)
        target_csv.parent.mkdir(parents=True, exist_ok=True)

        # 1. Write JSON Report
        with open(target_json, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        # 2. Write CSV Report
        fieldnames = [
            "document_id",
            "filename",
            "document_type",
            "status",
            "vendor_name_gt",
            "vendor_name_pred",
            "vendor_name_match",
            "invoice_number_gt",
            "invoice_number_pred",
            "invoice_number_match",
            "invoice_date_gt",
            "invoice_date_pred",
            "invoice_date_match",
            "subtotal_gt",
            "subtotal_pred",
            "subtotal_match",
            "tax_gt",
            "tax_pred",
            "tax_match",
            "grand_total_gt",
            "grand_total_pred",
            "grand_total_match",
            "overall_valid",
        ]

        records = detailed_records or []
        with open(target_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in records:
                writer.writerow(r)

        return target_json, target_csv

    @staticmethod
    def load_latest_evaluation() -> Optional[Dict[str, Any]]:
        """Loads the latest evaluation report from disk if present."""
        report_file = settings.evaluation_report_json
        if not report_file.exists():
            return None
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
