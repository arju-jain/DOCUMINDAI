import pytest
from backend.app.services.field_extractor import FieldExtractor


def test_extract_vendor_name_labeled():
    text = """
    From: Vanguard Systems Inc
    Invoice #: INV-100
    Date: 2026-05-10
    """
    extractor = FieldExtractor(text)
    vendor, conf, status = extractor.extract_vendor_name()
    assert vendor == "Vanguard Systems Inc"
    assert status == "extracted"
    assert conf is not None


def test_extract_vendor_name_header():
    text = """
    Apex Global Technologies
    100 Market St, San Francisco
    INVOICE
    Total: $500.00
    """
    extractor = FieldExtractor(text)
    vendor, conf, status = extractor.extract_vendor_name()
    assert vendor == "Apex Global Technologies"
    assert status == "extracted"


def test_extract_invoice_number_preserves_leading_zeros():
    text = "Invoice Number: 0004921\nDate: 2026-10-10"
    extractor = FieldExtractor(text)
    inv_num, conf, status = extractor.extract_invoice_number()
    assert inv_num == "0004921"
    assert isinstance(inv_num, str)
    assert status == "extracted"


def test_extract_invoice_number_alphanumeric():
    text = "Inv #: INV/2026-X99\nDate: 2026-10-10"
    extractor = FieldExtractor(text)
    inv_num, conf, status = extractor.extract_invoice_number()
    assert inv_num == "INV/2026-X99"


def test_extract_invoice_date_iso():
    text = "Invoice Date: 2026-10-15\nTotal: $100.00"
    extractor = FieldExtractor(text)
    d_val, conf, status = extractor.extract_invoice_date()
    assert d_val == "2026-10-15"
    assert status == "extracted"


def test_extract_invoice_date_named_month():
    text = "Date: 15 October 2026\nTotal: $100.00"
    extractor = FieldExtractor(text)
    d_val, conf, status = extractor.extract_invoice_date()
    assert d_val == "2026-10-15"


def test_extract_subtotal_and_tax_and_total():
    text = """
    Vendor: Acme Corp
    Invoice No: INV-123
    Date: 2026-04-10
    
    Subtotal: $1,450.00
    Tax (10%): $145.00
    Grand Total: $1,595.00
    """
    extractor = FieldExtractor(text)
    sub, sub_c, sub_s = extractor.extract_subtotal()
    tx, tx_c, tx_s = extractor.extract_tax()
    gt, gt_c, gt_s = extractor.extract_grand_total()

    assert sub == 1450.00
    assert tx == 145.00
    assert gt == 1595.00
    assert sub_s == "extracted"
    assert tx_s == "extracted"
    assert gt_s == "extracted"


def test_extract_split_cgst_sgst():
    text = """
    Subtotal: 1000.00
    CGST: 90.00
    SGST: 90.00
    Total: 1180.00
    """
    extractor = FieldExtractor(text)
    tx, conf, status = extractor.extract_tax()
    assert tx == 180.00
    assert status == "extracted"


def test_missing_field_returns_null_and_missing_status():
    text = "Just some unrelated text with no invoice fields."
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.vendor_name.value is None
    assert fields.vendor_name.status == "missing"
    assert fields.invoice_number.value is None
    assert fields.invoice_number.status == "missing"
    assert fields.subtotal.value is None
    assert fields.subtotal.status == "missing"


def test_classify_document_type():
    invoice_text = "Tax Invoice\nBill To: Client\nSubtotal: $100\nTotal: $110"
    non_invoice_text = "Hello world, this is a general meeting notes document."
    assert FieldExtractor(invoice_text).classify_document_type() == "invoice"
    assert FieldExtractor(non_invoice_text).classify_document_type() == "unknown"


def test_extract_complete_invoice():
    text = """
    From: Horizon Clean Energy Inc
    Invoice Number: HCE-3312
    Date of Issue: 2026-09-05
    Subtotal: $4,500.00
    Tax Amount: $450.00
    Grand Total: $4,950.00
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.vendor_name.value == "Horizon Clean Energy Inc"
    assert fields.vendor_name.status == "extracted"
    assert fields.invoice_number.value == "HCE-3312"
    assert fields.invoice_number.status == "extracted"
    assert fields.invoice_date.value == "2026-09-05"
    assert fields.invoice_date.status == "extracted"
    assert fields.subtotal.value == 4500.00
    assert fields.subtotal.status == "extracted"
    assert fields.tax.value == 450.00
    assert fields.tax.status == "extracted"
    assert fields.grand_total.value == 4950.00
    assert fields.grand_total.status == "extracted"


def test_extract_missing_tax():
    # Invoice without any tax mentioned
    text = """
    Vendor: Apex Industrial Supplies
    Invoice #: APX-8801
    Date: 2026-06-12
    Subtotal: $850.00
    Total: $850.00
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.vendor_name.value == "Apex Industrial Supplies"
    assert fields.invoice_number.value == "APX-8801"
    assert fields.invoice_date.value == "2026-06-12"
    assert fields.subtotal.value == 850.00
    # Tax MUST be None and missing (never fabricated or assumed to be 0.0)
    assert fields.tax.value is None
    assert fields.tax.status == "missing"
    assert fields.grand_total.value == 850.00


def test_extract_missing_invoice_number():
    # Document with no invoice number
    text = """
    From: Consulting Group LLC
    Date: 2026-07-20
    Base Amount: $1,200.00
    Tax: $120.00
    Total Due: $1,320.00
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.vendor_name.value == "Consulting Group LLC"
    assert fields.invoice_number.value is None
    assert fields.invoice_number.status == "missing"
    assert fields.invoice_date.value == "2026-07-20"
    assert fields.subtotal.value == 1200.00
    assert fields.tax.value == 120.00
    assert fields.grand_total.value == 1320.00


def test_extract_different_field_labels_and_currencies():
    # Alternative labels: Merchant, Bill #, Billing Date, Net Amount, VAT, Net Payable, EUR
    text = """
    Merchant: Continental Logistics GmbH
    Bill #: DE/2026/9021
    Billing Date: 24.11.2026
    Net Amount: €2.450,00
    VAT @ 19%: €465,50
    Net Payable: €2.915,50
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.vendor_name.value == "Continental Logistics GmbH"
    assert fields.invoice_number.value == "DE/2026/9021"
    assert fields.invoice_date.value == "2026-11-24"
    assert fields.subtotal.value == 2450.00
    assert fields.tax.value == 465.50
    assert fields.grand_total.value == 2915.50


def test_extract_inr_labels_and_named_month():
    # Alternative labels: Seller, Order ID, Date of Issue, Taxable Value, GST, Amount Due, INR
    text = """
    Seller: Bangalore Tech Solutions Pvt Ltd
    Order ID: ORD-99214
    Date of Issue: 18-August-2026
    Taxable Value: ₹50,000.00
    GST: ₹9,000.00
    Amount Due: ₹59,000.00
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.vendor_name.value == "Bangalore Tech Solutions Pvt Ltd"
    assert fields.invoice_number.value == "ORD-99214"
    assert fields.invoice_date.value == "2026-08-18"
    assert fields.subtotal.value == 50000.00
    assert fields.tax.value == 9000.00
    assert fields.grand_total.value == 59000.00


def test_extract_low_quality_scan():
    # OCR words with low confidence scores
    text = "Invoice Number: INV-9912\nDate: 2026-05-15\nTotal: $150.00"
    words_meta = [
        {"word": "INV-9912", "confidence": 0.40},
        {"word": "2026-05-15", "confidence": 0.35},
        {"word": "150.00", "confidence": 0.45},
    ]
    extractor = FieldExtractor(text, words_meta=words_meta, source_type="png", has_ocr=True)
    fields = extractor.extract_all()
    # Preserves extracted values while lowering confidence and setting status to low_confidence
    assert fields.invoice_number.value == "INV-9912"
    assert fields.invoice_number.confidence < 0.60
    assert fields.invoice_number.status == "low_confidence"

    assert fields.grand_total.value == 150.00
    assert fields.grand_total.confidence < 0.60
    assert fields.grand_total.status == "low_confidence"


def test_extract_invoice_with_only_a_total():
    # Simple slip / receipt containing only a total amount
    text = """
    Welcome to Corner Cafe
    Order #42
    Coffee               3.50
    Sandwich             6.50
    Total: $10.00
    Thank you!
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.grand_total.value == 10.00
    assert fields.grand_total.status == "extracted"
    assert fields.subtotal.value is None
    assert fields.subtotal.status == "missing"
    assert fields.tax.value is None
    assert fields.tax.status == "missing"
    assert fields.invoice_date.value is None
    assert fields.invoice_date.status == "missing"


def test_distinguish_ocr_failure_from_absent_field():
    # Label is present but value was unparseable / garbled due to OCR noise
    text = """
    Invoice No:
    Tax:
    Total: $100.00
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    # Invoice number label was detected -> needs_review, confidence=0.20
    assert fields.invoice_number.value is None
    assert fields.invoice_number.status == "needs_review"
    assert fields.invoice_number.confidence == 0.20

    # Tax label was detected -> needs_review, confidence=0.20
    assert fields.tax.value is None
    assert fields.tax.status == "needs_review"

    # Vendor was never mentioned at all -> missing, confidence=None
    assert fields.vendor_name.value is None
    assert fields.vendor_name.status == "missing"
    assert fields.vendor_name.confidence is None


def test_explicit_zero_tax_handling():
    # Explicit zero tax declared
    text = """
    Vendor: Acme Corp
    Invoice No: INV-100
    Date: 2026-10-10
    Subtotal: $500.00
    Tax: $0.00
    Total: $500.00
    """
    extractor = FieldExtractor(text)
    fields = extractor.extract_all()
    assert fields.tax.value == 0.0
    assert fields.tax.status == "extracted"

