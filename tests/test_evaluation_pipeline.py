import os
from pathlib import Path
import pytest

from evaluation.evaluate import (
    compare_date,
    compare_invoice_number,
    compare_numeric,
    compare_vendor,
    normalize_string,
    run_evaluation,
)
from backend.app.config import settings


def test_normalization_and_comparison_rules():
    # String normalization
    assert normalize_string("  TechCorp  Solutions  Inc. ") == "techcorp solutions inc."

    # Vendor comparison
    assert compare_vendor("TechCorp Solutions Inc", "techcorp solutions inc") is True
    assert compare_vendor("TechCorp", "TechCorp Solutions Inc") is True
    assert compare_vendor("Acme Corp", "Beta LLC") is False

    # Invoice number comparison (preserves leading zeros)
    assert compare_invoice_number("00142", "00142") is True
    assert compare_invoice_number("00142", "142") is False  # Must preserve leading zero
    assert compare_invoice_number("INV-2026", "inv-2026") is True

    # Date comparison
    assert compare_date("2026-10-15", "2026-10-15") is True
    assert compare_date("2026-10-15", "15/10/2026") is False  # Must be normalized ISO

    # Numeric comparison with rounding tolerance
    assert compare_numeric(100.0, 100.0) is True
    assert compare_numeric(100.00, 100.02, tolerance=0.05) is True
    assert compare_numeric(100.00, 100.10, tolerance=0.05) is False
    assert compare_numeric(None, None) is True
    assert compare_numeric(100.0, None) is False


def test_full_evaluation_execution():
    report = run_evaluation()
    assert report["status"] == "completed"
    assert report["total_documents"] >= 30
    assert report["successfully_processed"] >= 30
    assert report["overall_accuracy_percentage"] > 0.0

    # Verify both reports exist on disk
    assert settings.evaluation_report_json.exists()
    assert settings.evaluation_report_csv.exists()
