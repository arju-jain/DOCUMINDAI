import sys
import re
sys.path.insert(0, r"C:\Users\arjun\OneDrive\Desktop\multidocument")
from backend.app.services.field_extractor import FieldExtractor

# 1. Date test
text = "Invoice Date: 2026-10-15\nTotal: $100.00"
ext = FieldExtractor(text)
date_label_pattern = re.compile(
    r"(?:invoice\s+date|bill\s+date|billing\s+date|date\s+of\s+issue|issued\s+date|issue\s+date|doc(?:ument)?\s+date|txn\s+date|transaction\s+date|dated|date)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-\/]{6,25})",
    re.IGNORECASE,
)
m = date_label_pattern.search(ext.lines[0])
print("Date regex match on line 0:", m)
if m:
    raw_chunk = m.group(1).strip()
    print("raw_chunk:", repr(raw_chunk))
    iso = ext.parse_and_normalize_date(raw_chunk)
    print("parse_and_normalize_date:", repr(iso))

# 2. Subtotal test
subtotal_label = r"\b(?:sub\s*total|sub-total|subtotal|base\s+amount|net\s+amount|amount\s+before\s+tax|items\s+total|total\s+net|taxable\s+amount)\b"
amt_regex = r"(?:[\$€£₹¥]|rs\.?|inr|usd|eur|gbp|cad|aud)?\s*([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)"
compiled_sub = re.compile(rf"{subtotal_label}\s*[:\-]?\s*{amt_regex}", re.IGNORECASE)
line = "Subtotal: $1,450.00"
m_sub = compiled_sub.search(line)
print("Subtotal regex match on line:", m_sub)
if m_sub:
    print("m_sub groups:", m_sub.groups())
    raw_amt = m_sub.group(1).strip()
    print("raw_amt:", repr(raw_amt))
    val = ext._parse_monetary_value(raw_amt)
    print("parsed val:", val)
