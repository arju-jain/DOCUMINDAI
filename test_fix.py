import re

# 1. Test Date
date_label_pattern = re.compile(
    r"(?:invoice\s+date|bill\s+date|billing\s+date|date\s+of\s+issue|issued\s+date|issue\s+date|doc(?:ument)?\s+date|txn\s+date|transaction\s+date|dated|date)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-\/]{6,25})",
    re.IGNORECASE,
)
line1 = "Invoice Date: 2026-10-15\nTotal: $100.00"
line2 = "Date: 15 October 2026\nTotal: $100.00"
print("Date 1:", date_label_pattern.search(line1).group(1).strip())
print("Date 2:", date_label_pattern.search(line2).group(1).strip())

# 2. Test Amount
label_pattern = r"\b(?:sub\s*total|sub-total|subtotal|base\s+amount|net\s+amount|amount\s+before\s+tax)\b"
amt_regex = r"(?:[\$€£₹¥]|rs\.?|inr|usd|eur|gbp|cad|aud)?\s*([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)"
compiled = re.compile(rf"{label_pattern}\s*[:\-]?\s*{amt_regex}", re.IGNORECASE)

line3 = "Subtotal: $1,450.00"
m = compiled.search(line3)
print("Amount 3:", m.group(1).strip())

# 3. Test Tax
tax_label = r"\b(?:total\s+tax|tax\s+amount|vat\s+amount|gst\s+amount|sales\s+tax|vat|gst|tax|hst|pst)\b(?:\s*\(.*?\)|@?\s*\d+%)?"
compiled_tax = re.compile(rf"{tax_label}\s*[:\-]?\s*{amt_regex}", re.IGNORECASE)
line4 = "Tax (10%): $145.00"
m4 = compiled_tax.search(line4)
print("Tax 4:", m4.group(1).strip())
