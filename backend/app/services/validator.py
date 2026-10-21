import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from backend.app.config import settings
from backend.app.schemas import (
    ExtractedFields,
    ValidationIssue,
    ValidationResult,
)


class InvoiceValidator:
    """Dedicated business logic validator for invoice dates, monetary precision,
    required fields, low-confidence warnings, and invoice arithmetic.
    """

    REQUIRED_FIELDS = ["invoice_number", "invoice_date", "grand_total"]

    def __init__(self, fields: ExtractedFields, tolerance: float = None, raw_text: Optional[str] = None):
        self.fields = fields
        self.tolerance = tolerance if tolerance is not None else settings.rounding_tolerance
        self.raw_text = raw_text or ""
        self.issues: List[ValidationIssue] = []

    def validate(self) -> Tuple[ExtractedFields, ValidationResult]:
        """Runs all validation rules and updates field statuses while preserving extracted values."""
        has_invalid = False
        has_needs_review = False

        # 1. Required Fields Check
        for req_field in self.REQUIRED_FIELDS:
            field_obj = getattr(self.fields, req_field, None)
            if field_obj is None or field_obj.value is None or field_obj.status == "missing":
                self.issues.append(
                    ValidationIssue(
                        field=req_field,
                        code="REQUIRED_FIELD_MISSING",
                        message=f"Required field '{req_field}' is missing from the document.",
                    )
                )
                has_invalid = True

        # 2. Date Validation
        date_obj = self.fields.invoice_date
        if date_obj and date_obj.value is not None:
            is_valid, msg = self._validate_date(date_obj.value)
            if not is_valid:
                date_obj.status = "invalid"
                self.issues.append(
                    ValidationIssue(
                        field="invoice_date",
                        code="INVALID_DATE",
                        message=msg,
                    )
                )
                has_invalid = True

        # 3. Monetary Values Validation
        for num_field in ["subtotal", "tax", "grand_total"]:
            f_obj = getattr(self.fields, num_field)
            if f_obj and f_obj.value is not None:
                if f_obj.value < 0:
                    f_obj.status = "invalid"
                    self.issues.append(
                        ValidationIssue(
                            field=num_field,
                            code="NEGATIVE_AMOUNT",
                            message=f"Monetary value for '{num_field}' cannot be negative ({f_obj.value}).",
                        )
                    )
                    has_invalid = True

        # 4. Arithmetic Consistency Check
        arithmetic_status, arithmetic_issue = self._check_arithmetic()
        if arithmetic_issue:
            self.issues.append(arithmetic_issue)
            if arithmetic_status == "invalid":
                has_invalid = True
                if self.fields.grand_total.status != "invalid":
                    self.fields.grand_total.status = "needs_review"
            elif arithmetic_status == "needs_review":
                has_needs_review = True

        # 5. Low Confidence Flags
        for name in ["vendor_name", "invoice_number", "invoice_date", "subtotal", "tax", "grand_total"]:
            f_obj = getattr(self.fields, name)
            if f_obj and f_obj.value is not None:
                if f_obj.status == "low_confidence":
                    has_needs_review = True
                    self.issues.append(
                        ValidationIssue(
                            field=name,
                            code="LOW_CONFIDENCE",
                            message=f"Field '{name}' was extracted with low confidence ({f_obj.confidence:.2f}).",
                        )
                    )

        # 6. Overall Status Determination
        if has_invalid:
            overall_status = "invalid"
        elif has_needs_review:
            overall_status = "needs_review"
        else:
            overall_status = "valid"

        return self.fields, ValidationResult(overall_status=overall_status, issues=self.issues)

    def _validate_date(self, date_str: str) -> Tuple[bool, str]:
        """Validates that the date represents a plausible, valid calendar date."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # Plausibility check: not earlier than 1990 and not beyond 2040
            if dt.year < 1990:
                return False, f"Date {date_str} is earlier than permissible minimum (1990)."
            if dt.year > 2040:
                return False, f"Date {date_str} is beyond plausible future range (2040)."
            return True, ""
        except ValueError:
            return False, f"Date '{date_str}' is not a valid ISO date."

    def _check_arithmetic(self) -> Tuple[str, ValidationIssue]:
        """Verifies if subtotal + tax ≈ grand_total within the documented rounding tolerance.
        Does not assume every document has subtotal or tax; if missing, returns unverifiable
        warning rather than invalidating the document.
        """
        st = self.fields.subtotal.value
        tx = self.fields.tax.value
        gt = self.fields.grand_total.value

        if gt is None:
            return "none", None

        # If subtotal or tax is missing, arithmetic cannot be verified
        if st is None or tx is None:
            missing_parts = []
            if st is None:
                missing_parts.append("subtotal")
            if tx is None:
                missing_parts.append("tax")
            return "needs_review", ValidationIssue(
                field="grand_total",
                code="ARITHMETIC_UNVERIFIABLE",
                message=f"Arithmetic check unavailable because {', '.join(missing_parts)} was not extracted.",
            )

        # Perform precise Decimal calculation to prevent floating point inaccuracy
        try:
            d_st = Decimal(str(st))
            d_tx = Decimal(str(tx))
            d_gt = Decimal(str(gt))
            expected = d_st + d_tx
            diff = abs(d_gt - expected)
            tol = Decimal(str(self.tolerance))

            if diff > tol:
                adj_patterns = re.compile(
                    r"\b(?:discount|coupon|promo|rebate|less|off|markdown|credit|shipping|freight|delivery|handling|fee|surcharge|service\s+charge|tip|gratuity|convenience\s+fee)\b",
                    re.IGNORECASE,
                )
                if self.raw_text and adj_patterns.search(self.raw_text):
                    return "needs_review", ValidationIssue(
                        field="grand_total",
                        code="TOTAL_MISMATCH_WITH_ADJUSTMENTS",
                        message=(
                            f"The extracted grand total ({gt}) differs from calculated subtotal ({st}) + tax ({tx}) = {float(expected):.2f} "
                            f"by {float(diff):.2f}. The document text indicates additional charges, shipping, or discounts may apply."
                        ),
                    )

                return "invalid", ValidationIssue(
                    field="grand_total",
                    code="TOTAL_MISMATCH",
                    message=(
                        f"The extracted grand total ({gt}) does not match the calculated amount "
                        f"({float(expected):.2f} = subtotal {st} + tax {tx})."
                    ),
                )
        except Exception as e:
            return "needs_review", ValidationIssue(
                field="grand_total",
                code="CALCULATION_ERROR",
                message=f"Could not compute arithmetic consistency: {str(e)}",
            )

        return "valid", None
