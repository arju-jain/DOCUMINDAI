import pytest
from backend.app.schemas import ExtractedFields, NumericField, StringField
from backend.app.services.validator import InvoiceValidator


def test_validator_perfect_invoice():
    fields = ExtractedFields(
        vendor_name=StringField(value="Acme Corp", confidence=0.95, status="extracted"),
        invoice_number=StringField(value="INV-101", confidence=0.98, status="extracted"),
        invoice_date=StringField(value="2026-10-15", confidence=0.95, status="extracted"),
        subtotal=NumericField(value=100.0, confidence=0.97, status="extracted"),
        tax=NumericField(value=15.0, confidence=0.96, status="extracted"),
        grand_total=NumericField(value=115.0, confidence=0.98, status="extracted"),
    )
    validator = InvoiceValidator(fields=fields)
    v_fields, result = validator.validate()
    assert result.overall_status == "valid"
    assert len(result.issues) == 0


def test_validator_arithmetic_mismatch():
    # 100 + 10 != 125
    fields = ExtractedFields(
        vendor_name=StringField(value="Acme Corp", confidence=0.95, status="extracted"),
        invoice_number=StringField(value="INV-101", confidence=0.98, status="extracted"),
        invoice_date=StringField(value="2026-10-15", confidence=0.95, status="extracted"),
        subtotal=NumericField(value=100.0, confidence=0.97, status="extracted"),
        tax=NumericField(value=10.0, confidence=0.96, status="extracted"),
        grand_total=NumericField(value=125.0, confidence=0.98, status="extracted"),
    )
    validator = InvoiceValidator(fields=fields)
    v_fields, result = validator.validate()
    assert result.overall_status == "invalid"
    # Preserves grand_total value, sets status to needs_review or invalid
    assert v_fields.grand_total.value == 125.0
    assert any(i.code == "TOTAL_MISMATCH" for i in result.issues)


def test_validator_missing_required_field():
    fields = ExtractedFields(
        vendor_name=StringField(value="Acme Corp", confidence=0.95, status="extracted"),
        invoice_number=StringField(value=None, confidence=None, status="missing"),
        invoice_date=StringField(value="2026-10-15", confidence=0.95, status="extracted"),
        subtotal=NumericField(value=100.0, confidence=0.97, status="extracted"),
        tax=NumericField(value=10.0, confidence=0.96, status="extracted"),
        grand_total=NumericField(value=110.0, confidence=0.98, status="extracted"),
    )
    validator = InvoiceValidator(fields=fields)
    v_fields, result = validator.validate()
    assert result.overall_status == "invalid"
    assert any(i.code == "REQUIRED_FIELD_MISSING" and i.field == "invoice_number" for i in result.issues)


def test_validator_impossible_date():
    fields = ExtractedFields(
        vendor_name=StringField(value="Acme Corp", confidence=0.95, status="extracted"),
        invoice_number=StringField(value="INV-101", confidence=0.98, status="extracted"),
        invoice_date=StringField(value="2026-02-30", confidence=0.95, status="extracted"),
        subtotal=NumericField(value=100.0, confidence=0.97, status="extracted"),
        tax=NumericField(value=10.0, confidence=0.96, status="extracted"),
        grand_total=NumericField(value=110.0, confidence=0.98, status="extracted"),
    )
    validator = InvoiceValidator(fields=fields)
    v_fields, result = validator.validate()
    assert result.overall_status == "invalid"
    assert v_fields.invoice_date.status == "invalid"
    assert any(i.code == "INVALID_DATE" for i in result.issues)


def test_validator_unverifiable_arithmetic_does_not_invalidate():
    # Tax missing -> arithmetic check cannot be completed, but should not be marked invalid
    fields = ExtractedFields(
        vendor_name=StringField(value="Acme Corp", confidence=0.95, status="extracted"),
        invoice_number=StringField(value="INV-101", confidence=0.98, status="extracted"),
        invoice_date=StringField(value="2026-10-15", confidence=0.95, status="extracted"),
        subtotal=NumericField(value=100.0, confidence=0.97, status="extracted"),
        tax=NumericField(value=None, confidence=None, status="missing"),
        grand_total=NumericField(value=100.0, confidence=0.98, status="extracted"),
    )
    validator = InvoiceValidator(fields=fields)
    v_fields, result = validator.validate()
    assert result.overall_status == "needs_review"
    assert any(i.code == "ARITHMETIC_UNVERIFIABLE" for i in result.issues)


def test_validator_low_confidence_flag():
    fields = ExtractedFields(
        vendor_name=StringField(value="Acme Corp", confidence=0.45, status="low_confidence"),
        invoice_number=StringField(value="INV-101", confidence=0.98, status="extracted"),
        invoice_date=StringField(value="2026-10-15", confidence=0.95, status="extracted"),
        subtotal=NumericField(value=100.0, confidence=0.97, status="extracted"),
        tax=NumericField(value=10.0, confidence=0.96, status="extracted"),
        grand_total=NumericField(value=110.0, confidence=0.98, status="extracted"),
    )
    validator = InvoiceValidator(fields=fields)
    v_fields, result = validator.validate()
    assert result.overall_status == "needs_review"
    assert any(i.code == "LOW_CONFIDENCE" and i.field == "vendor_name" for i in result.issues)


def test_validator_arithmetic_with_discount_or_shipping():
    # 100 + 10 = 110, but grand_total is 105 due to $5 discount
    fields = ExtractedFields(
        vendor_name=StringField(value="Acme Corp", confidence=0.95, status="extracted"),
        invoice_number=StringField(value="INV-101", confidence=0.98, status="extracted"),
        invoice_date=StringField(value="2026-10-15", confidence=0.95, status="extracted"),
        subtotal=NumericField(value=100.0, confidence=0.97, status="extracted"),
        tax=NumericField(value=10.0, confidence=0.96, status="extracted"),
        grand_total=NumericField(value=105.0, confidence=0.98, status="extracted"),
    )
    raw_text = "Subtotal: $100.00\nTax: $10.00\nSpecial Discount: -$5.00\nGrand Total: $105.00"
    validator = InvoiceValidator(fields=fields, raw_text=raw_text)
    v_fields, result = validator.validate()
    # Does not fail the entire document as hard invalid when discount is present
    assert result.overall_status == "needs_review"
    assert any(i.code == "TOTAL_MISMATCH_WITH_ADJUSTMENTS" for i in result.issues)

