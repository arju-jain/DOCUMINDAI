import sys
import re
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
print("Lines in extractor:")
for idx, l in enumerate(extractor.lines):
    print(f"{idx}: {repr(l)}")

label_pattern = r"\b(?:sub\s*total|sub-total|subtotal|base\s+amount|net\s+amount|amount\s+before\s+tax|items\s+total|total\s+net|taxable\s+amount)\b"
curr = r"(?:[\$€£₹¥]|rs\.?|inr|usd|eur|gbp|cad|aud|sgd|aed|jpy|chf|cny)?"
amt_regex = r"([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?|[0-9]+)"
compiled = re.compile(rf"{label_pattern}\s*[:\-]?\s*{curr}\s*{amt_regex}", re.IGNORECASE)

line = extractor.lines[3]
print("Matching line:", repr(line))
m = compiled.search(line)
print("m:", m)
if m:
    print("m.group(1):", m.group(1))

sub = extractor.extract_subtotal()
print("extract_subtotal result:", sub)
