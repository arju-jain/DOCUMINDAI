import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

# Let's test full FieldExtractor implementation logic
MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

def parse_and_normalize_date(fragment: str):
    fragment = fragment.strip().rstrip(".,;:")
    m_iso = re.search(r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", fragment)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}"

    month_regex = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    m_dmy = re.search(rf"\b(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[\s\-,/]+{month_regex}[\s\-,/]+(20\d{{2}})\b", fragment, re.IGNORECASE)
    if m_dmy:
        d = int(m_dmy.group(1))
        m_str = m_dmy.group(2).lower()
        m = MONTH_NAMES.get(m_str)
        y = int(m_dmy.group(3))
        if m:
            return f"{y:04d}-{m:02d}-{d:02d}"

    m_mdy = re.search(rf"\b{month_regex}[\s\-,/]+(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[\s\-,/]+(20\d{{2}})\b", fragment, re.IGNORECASE)
    if m_mdy:
        m_str = m_mdy.group(1).lower()
        m = MONTH_NAMES.get(m_str)
        d = int(m_mdy.group(2))
        y = int(m_mdy.group(3))
        if m:
            return f"{y:04d}-{m:02d}-{d:02d}"

    m_num = re.search(r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|[12]\d|3[01])[-/.](20\d{2})\b", fragment)
    if m_num:
        p1, p2, year = int(m_num.group(1)), int(m_num.group(2)), int(m_num.group(3))
        if p1 > 12 and p2 <= 12:
            return f"{year:04d}-{p2:02d}-{p1:02d}"
        if p2 > 12 and p1 <= 12:
            return f"{year:04d}-{p1:02d}-{p2:02d}"
        if p1 == p2:
            return f"{year:04d}-{p1:02d}-{p2:02d}"
        if "." in m_num.group(0):
            return f"{year:04d}-{p2:02d}-{p1:02d}"
    return None

print("ISO test:", parse_and_normalize_date("2026-10-15"))
print("Named test:", parse_and_normalize_date("15 October 2026"))
print("Dots test:", parse_and_normalize_date("15.10.2026"))
