import sys
import re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\arjun\OneDrive\Desktop\multidocument")
from backend.app.services.field_extractor import FieldExtractor

text = """
Vendor: Acme Corp
Invoice No: INV-123
Date: 2026-04-10

Subtotal: $1,450.00
Tax (10%): $145.00
Grand Total: $1,595.00
"""

extractor = FieldExtractor(text)
label_pattern = r"\b(?:sub\s*total|sub-total|subtotal|base\s+amount|net\s+amount|amount\s+before\s+tax|items\s+total|total\s+net|taxable\s+amount)\b"

curr = r"(?:[\$€£₹¥]|rs\.?|inr|usd|eur|gbp|cad|aud|sgd|aed|jpy|chf|cny)?"
amt_regex = r"([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?|[0-9]+)"
compiled = re.compile(rf"{label_pattern}\s*[:\-]?\s*{curr}\s*{amt_regex}", re.IGNORECASE)

for i, line in enumerate(extractor.lines):
    m = compiled.search(line)
    print(f"Line {i} ({line}): match={m}")
    if m:
        raw_amt = m.group(1).strip()
        val = extractor._parse_monetary_value(raw_amt)
        print(f"  raw_amt={raw_amt}, parsed_val={val}")

res = extractor.extract_subtotal()
print("extract_subtotal:", res)
