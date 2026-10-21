target_path = r"C:\Users\arjun\OneDrive\Desktop\multidocument\backend\app\services\field_extractor.py"

extractor_code = '''import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from backend.app.schemas import (
    ExtractedFields,
    NumericField,
    StringField,
)
from backend.app.services.confidence import ConfidenceScorer


class FieldExtractor:
    """Modular extraction engine for invoice fields with contextual label matching,
    regex pattern detection, date normalization, multiline layout support,
    and distinction between genuinely absent fields vs OCR recognition failures.
    """

    MONTH_NAMES = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    IGNORE_VENDOR_PATTERNS = [
        r"^invoice",
        r"^tax\s+invoice",
        r"^bill\s+to",
        r"^ship\s+to",
        r"^sold\s+to",
        r"^date",
        r"^total",
        r"^subtotal",
        r"^amount",
        r"^purchase\s+order",
        r"^page\s+\d+",
        r"^original\s+for\s+recipient",
        r"^duplicate\s+for\s+transporter",
        r"^estimate",
        r"^receipt",
    ]

    def __init__(self, raw_text: str, words_meta: Optional[List[Dict[str, Any]]] = None, source_type: str = "pdf", has_ocr: bool = False):
        self.raw_text = raw_text or ""
        self.lines = [line.strip() for line in self.raw_text.splitlines() if line.strip()]
        self.words_meta = words_meta or []
        self.source_type = source_type
        self.has_ocr = has_ocr

    def classify_document_type(self) -> str:
        """Determines the document type based on structural and contextual keywords."""
        lower = self.raw_text.lower()
        invoice_signals = [
            "invoice", "tax invoice", "bill to", "due date", "amount due",
            "subtotal", "grand total", "total amount", "gstin", "vat reg",
            "invoice no", "inv #", "invoice #", "remit to", "balance due",
            "order number", "order id", "receipt", "merchant", "total due"
        ]
        score = sum(1 for s in invoice_signals if s in lower)
        if score >= 2 or "invoice" in lower or "receipt" in lower or "tax invoice" in lower:
            return "invoice"
        return "unknown"

    def _find_word_confidences_for_text(self, text_val: str) -> List[float]:
        """Looks up word confidences from OCR metadata matching the extracted string tokens."""
        if not self.words_meta or not text_val:
            return []
        tokens = [t.lower().strip(".,:;!?#$€£₹¥") for t in text_val.split() if t.strip(".,:;!?#$€£₹¥")]
        if not tokens:
            return []
        
        confidences = []
        for meta in self.words_meta:
            clean_word = (meta.get("word") or "").lower().strip(".,:;!?#$€£₹¥")
            if clean_word in tokens and meta.get("confidence") is not None:
                confidences.append(float(meta["confidence"]))
        return confidences

    # =========================================================================
    # VENDOR NAME EXTRACTION
    # =========================================================================
    def extract_vendor_name(self) -> Tuple[Optional[str], Optional[float], str]:
        """Extracts vendor / seller / merchant name from explicit labels or top headers.
        Distinguishes missing vendor from label present but unparseable (needs_review).
        """
        # 1. Check explicit label (same-line or adjacent next line)
        label_pattern = re.compile(
            r"^(?:from|vendor|seller|merchant|biller|provider|issuer|supplier|store|shop|contractor|billed\s+by|sold\s+by|issued\s+by|company)\s*[:\-]\s*(.*)$",
            re.IGNORECASE,
        )

        label_detected = False
        for i, line in enumerate(self.lines[:20]):
            m = label_pattern.search(line)
            if m:
                label_detected = True
                candidate = m.group(1).strip()
                # If value is on same line
                if candidate and self._is_valid_vendor(candidate, is_labeled=True):
                    confs = self._find_word_confidences_for_text(candidate)
                    confidence = ConfidenceScorer.calculate_field_confidence(
                        self.source_type, self.has_ocr, confs, label_match_type="exact", pattern_match_type="strict"
                    )
                    status = ConfidenceScorer.determine_status(candidate, confidence)
                    return candidate, confidence, status
                # If value is on next line
                if (not candidate or len(candidate) < 2) and i + 1 < len(self.lines):
                    next_line = self.lines[i + 1].strip()
                    if self._is_valid_vendor(next_line, is_labeled=True):
                        confs = self._find_word_confidences_for_text(next_line)
                        confidence = ConfidenceScorer.calculate_field_confidence(
                            self.source_type, self.has_ocr, confs, label_match_type="exact", pattern_match_type="moderate"
                        )
                        status = ConfidenceScorer.determine_status(next_line, confidence)
                        return next_line, confidence, status

        # 2. Look for top non-noise header line in the first 8 lines
        for line in self.lines[:8]:
            if self._is_valid_vendor(line):
                # Clean up any trailing tags or table dividers
                candidate = re.split(r"\s{2,}|\,|\|", line)[0].strip()
                if self._is_valid_vendor(candidate):
                    confs = self._find_word_confidences_for_text(candidate)
                    confidence = ConfidenceScorer.calculate_field_confidence(
                        self.source_type, self.has_ocr, confs, label_match_type="header", pattern_match_type="moderate"
                    )
                    status = ConfidenceScorer.determine_status(candidate, confidence)
                    return candidate, confidence, status

        # 3. If an explicit vendor label was detected in the document but no valid name parsed:
        if label_detected:
            return None, 0.20, "needs_review"

        # 4. Genuinely absent
        return None, None, "missing"

    def _is_valid_vendor(self, candidate: str, is_labeled: bool = False) -> bool:
        if not candidate or len(candidate) < 3 or len(candidate) > 70:
            return False
        c_lower = candidate.lower()
        for pat in self.IGNORE_VENDOR_PATTERNS:
            if re.search(pat, c_lower):
                return False
        # Must contain letters
        if not re.search(r"[a-zA-Z]", candidate):
            return False
        # Should not be a pure date, address postal code, or monetary line
        if re.search(r"^\d+[\s\-\/\.]\d+", candidate) or re.search(r"^[\$\€\£\₹\¥]\s*\d+", candidate):
            return False

        # If it was matched via explicit label (e.g. From: or Merchant:), accept directly
        if is_labeled:
            return True

        # For unlabeled header fallback:
        # A vendor name should not be a long sentence (limit to <= 6 words)
        words = candidate.split()
        if len(words) > 6:
            return False

        # Check for sentence markers like full stops or lowercase articles/prepositions dominating
        common_sentence_words = {"some", "with", "this", "that", "these", "those", "have", "from", "just", "hello", "notes", "unrelated", "welcome", "thank"}
        if any(w.lower() in common_sentence_words for w in words):
            return False

        # Business entity indicators
        biz_suffixes = [
            "inc", "llc", "ltd", "corp", "corporation", "co", "company", "solutions",
            "technologies", "systems", "group", "enterprises", "services", "labs",
            "logistics", "consulting", "works", "retail", "associates", "partners",
            "pvt", "pvt ltd", "private limited", "gmbh", "s.a.", "s.l.", "b.v.", "pte", "plc", "llp", "market", "store", "shop"
        ]
        has_biz_suffix = any(w.lower().rstrip(".,") in biz_suffixes for w in words)
        
        # If no business suffix, require title case for alphabetic words
        is_title_case = all(w[0].isupper() for w in words if w[0].isalpha())

        return has_biz_suffix or is_title_case

    # =========================================================================
    # INVOICE NUMBER EXTRACTION
    # =========================================================================
    def extract_invoice_number(self) -> Tuple[Optional[str], Optional[float], str]:
        """Extracts the invoice / bill / order number, preserving all characters including leading zeros.
        Distinguishes missing invoice number from label present but unparseable (needs_review).
        """
        label_keyword_regex = re.compile(
            r"\b(?:invoice\s+(?:number|no|num|id|#)|inv\s+(?:number|no|num|id|#)|bill\s+(?:number|no|num|#)|receipt\s+(?:number|no|#)|order\s+(?:number|id|#)|doc(?:ument)?\s+(?:number|no|num|#)|ref(?:erence)?\s+(?:number|no|#)|folio\s+(?:number|no|#)|voucher\s+(?:number|no|#)|transaction\s+(?:id|number|no|#)|txn\s+(?:id|number|no|#)|invoice\s*#)\b",
            re.IGNORECASE
        )

        patterns = [
            # Strict contextual labels: "Invoice No: INV-1025", "Invoice #: 00124", "Inv No. #1024"
            r"(?:invoice\s+(?:number|no|num|id|#)|inv\s+(?:number|no|num|id|#)|bill\s+(?:number|no|num|#)|receipt\s+(?:number|no|#)|order\s+(?:number|id|#)|doc(?:ument)?\s+(?:number|no|num|#)|ref(?:erence)?\s+(?:number|no|#)|folio\s+(?:number|no|#)|voucher\s+(?:number|no|#)|transaction\s+(?:id|number|no|#)|txn\s+(?:id|number|no|#)|invoice\s*#)\s*[:\-#]?\s*([A-Za-z0-9][A-Za-z0-9\-\_\/\.\#]{1,30})",
            # Standalone label on previous or adjacent tokens
            r"(?:invoice\s+no\b|inv\s*#|bill\s+no\b|order\s+id\b)\s*[:\-]?\s*([A-Za-z0-9\-\_\/\.\#]+)",
        ]

        label_detected = False

        # 1. Search for same-line patterns
        for pat in patterns:
            for line in self.lines:
                if label_keyword_regex.search(line):
                    label_detected = True

                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    val = m.group(1).strip().rstrip(".,;:)")
                    if len(val) >= 2 and val.lower() not in ("date", "total", "tax", "due", "subtotal", "amount"):
                        confs = self._find_word_confidences_for_text(val)
                        confidence = ConfidenceScorer.calculate_field_confidence(
                            self.source_type, self.has_ocr, confs, label_match_type="exact", pattern_match_type="strict"
                        )
                        status = ConfidenceScorer.determine_status(val, confidence)
                        return val, confidence, status

        # 2. Check for two-column or stacked layout: Label on line i, number on line i+1
        label_only = re.compile(r"^(?:invoice\s+(?:number|no|num|id|#)|inv\s+(?:number|no|num|id|#)|bill\s+(?:number|no|num|#)|receipt\s+(?:number|no|#)|order\s+(?:number|id|#))\s*[:\-#]?$", re.IGNORECASE)
        for i, line in enumerate(self.lines):
            if label_only.search(line):
                label_detected = True
                if i + 1 < len(self.lines):
                    next_line = self.lines[i + 1].strip()
                    m_next = re.search(r"^#?\s*([A-Za-z0-9][A-Za-z0-9\-\_\/\.\#]{1,30})$", next_line)
                    if m_next:
                        val = m_next.group(1).strip().rstrip(".,;:)")
                        if len(val) >= 2 and val.lower() not in ("date", "total", "tax", "due", "subtotal", "amount"):
                            confs = self._find_word_confidences_for_text(val)
                            confidence = ConfidenceScorer.calculate_field_confidence(
                                self.source_type, self.has_ocr, confs, label_match_type="exact", pattern_match_type="moderate"
                            )
                            status = ConfidenceScorer.determine_status(val, confidence)
                            return val, confidence, status

        # 3. If label was present in document but extraction failed (e.g. illegible scan / OCR noise)
        if label_detected or label_keyword_regex.search(self.raw_text):
            return None, 0.20, "needs_review"

        # 4. Genuinely absent
        return None, None, "missing"

    # =========================================================================
    # INVOICE DATE EXTRACTION
    # =========================================================================
    def extract_invoice_date(self) -> Tuple[Optional[str], Optional[float], str]:
        """Extracts and normalizes invoice date to ISO YYYY-MM-DD when unambiguous.
        Supports alternative labels (Billing Date, Txn Date, Date of Issue) and stacked layouts.
        Distinguishes missing date from label present but unparseable.
        """
        date_label_pattern = re.compile(
            r"(?:invoice\s+date|bill\s+date|billing\s+date|date\s+of\s+issue|issued\s+date|issue\s+date|doc(?:ument)?\s+date|txn\s+date|transaction\s+date|dated|date)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-\/]{6,25})",
            re.IGNORECASE,
        )

        candidates = []
        for line in self.lines:
            m = date_label_pattern.search(line)
            if m:
                raw_chunk = m.group(1).strip()
                parsed_iso = self.parse_and_normalize_date(raw_chunk)
                if parsed_iso:
                    candidates.append((parsed_iso, raw_chunk, "exact"))

        # Check adjacent next line if label is on its own line
        if not candidates:
            label_only = re.compile(r"^(?:invoice\s+date|bill\s+date|billing\s+date|date\s+of\s+issue|date)\s*[:\-]?$", re.IGNORECASE)
            for i, line in enumerate(self.lines):
                if label_only.search(line) and i + 1 < len(self.lines):
                    next_line = self.lines[i + 1].strip()
                    parsed_iso = self.parse_and_normalize_date(next_line)
                    if parsed_iso:
                        candidates.append((parsed_iso, next_line, "fuzzy"))
                        break

        # If no labeled date candidate, scan for isolated unambiguous ISO dates (YYYY-MM-DD)
        if not candidates:
            iso_pattern = re.compile(r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b")
            for line in self.lines:
                m = iso_pattern.search(line)
                if m:
                    parsed_iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                    candidates.append((parsed_iso, m.group(0), "none"))
                    break

        if candidates:
            iso_val, raw_matched, match_type = candidates[0]
            confs = self._find_word_confidences_for_text(raw_matched)
            confidence = ConfidenceScorer.calculate_field_confidence(
                self.source_type, self.has_ocr, confs, label_match_type=match_type, pattern_match_type="strict"
            )
            status = ConfidenceScorer.determine_status(iso_val, confidence)
            return iso_val, confidence, status

        # If date label was detected in document but date was unparseable
        date_label_kw = re.compile(r"\b(?:invoice\s+date|bill\s+date|billing\s+date|date\s+of\s+issue|issued\s+date|issue\s+date|dated|date)\b", re.IGNORECASE)
        if date_label_kw.search(self.raw_text):
            return None, 0.20, "needs_review"

        return None, None, "missing"

    def parse_and_normalize_date(self, text_fragment: str) -> Optional[str]:
        """Attempts unambiguous conversion of varied date formats to ISO YYYY-MM-DD.
        Supports ISO, named month formats, and numeric dotted/slashed formats.
        Rejects ambiguous dates where day and month cannot be determined.
        """
        fragment = text_fragment.strip().rstrip(".,;:")
        
        # 1. ISO format: YYYY-MM-DD or YYYY/MM/DD
        m_iso = re.search(r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", fragment)
        if m_iso:
            y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
            if self._is_valid_calendar_date(y, m, d):
                return f"{y:04d}-{m:02d}-{d:02d}"

        # 2. Named month formats: e.g., "15 Oct 2026", "October 15, 2026", "15-October-2026", "Oct 15, 2026"
        month_regex = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        
        # Day Month Year: "15 Oct 2026", "15-Oct-2026", "15th October 2026"
        m_dmy = re.search(rf"\b(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[\s\-,/]+{month_regex}[\s\-,/]+(20\d{{2}})\b", fragment, re.IGNORECASE)
        if m_dmy:
            d = int(m_dmy.group(1))
            m_str = m_dmy.group(2).lower()
            m = self.MONTH_NAMES.get(m_str)
            y = int(m_dmy.group(3))
            if m and self._is_valid_calendar_date(y, m, d):
                return f"{y:04d}-{m:02d}-{d:02d}"

        # Month Day Year: "Oct 15, 2026", "October 15 2026"
        m_mdy = re.search(rf"\b{month_regex}[\s\-,/]+(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[\s\-,/]+(20\d{{2}})\b", fragment, re.IGNORECASE)
        if m_mdy:
            m_str = m_mdy.group(1).lower()
            m = self.MONTH_NAMES.get(m_str)
            d = int(m_mdy.group(2))
            y = int(m_mdy.group(3))
            if m and self._is_valid_calendar_date(y, m, d):
                return f"{y:04d}-{m:02d}-{d:02d}"

        # Year Month Day named: "2026-Oct-15"
        m_ymd_name = re.search(rf"\b(20\d{{2}})[\s\-,/]+{month_regex}[\s\-,/]+(0?[1-9]|[12]\d|3[01])\b", fragment, re.IGNORECASE)
        if m_ymd_name:
            y = int(m_ymd_name.group(1))
            m_str = m_ymd_name.group(2).lower()
            m = self.MONTH_NAMES.get(m_str)
            d = int(m_ymd_name.group(3))
            if m and self._is_valid_calendar_date(y, m, d):
                return f"{y:04d}-{m:02d}-{d:02d}"

        # 3. Numeric slashed/dotted formats: DD/MM/YYYY, DD.MM.YYYY, MM/DD/YYYY
        m_num = re.search(r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|[12]\d|3[01])[-/.](20\d{2})\b", fragment)
        if m_num:
            part1 = int(m_num.group(1))
            part2 = int(m_num.group(2))
            year = int(m_num.group(3))

            # If part1 > 12, it must be DD/MM/YYYY (unambiguous)
            if part1 > 12 and part2 <= 12:
                if self._is_valid_calendar_date(year, part2, part1):
                    return f"{year:04d}-{part2:02d}-{part1:02d}"

            # If part2 > 12, it must be MM/DD/YYYY (unambiguous)
            if part2 > 12 and part1 <= 12:
                if self._is_valid_calendar_date(year, part1, part2):
                    return f"{year:04d}-{part1:02d}-{part2:02d}"

            # If part1 == part2 (e.g. 05/05/2026), it is unambiguous
            if part1 == part2 and self._is_valid_calendar_date(year, part1, part2):
                return f"{year:04d}-{part1:02d}-{part2:02d}"

            # In European/International dot format (DD.MM.YYYY), standard convention is DD.MM.YYYY
            if "." in m_num.group(0):
                if self._is_valid_calendar_date(year, part2, part1):
                    return f"{year:04d}-{part2:02d}-{part1:02d}"

        return None

    @staticmethod
    def _is_valid_calendar_date(y: int, m: int, d: int) -> bool:
        try:
            datetime(y, m, d)
            return True
        except ValueError:
            return False

    # =========================================================================
    # MONETARY AMOUNTS EXTRACTION (Subtotal, Tax, Grand Total)
    # =========================================================================
    def _parse_monetary_value(self, raw_str: str) -> Optional[float]:
        """Extracts clean numeric value preserving decimal precision, handling multi-currency symbols and commas."""
        if not raw_str:
            return None
        # Remove currency symbols ($ € £ ₹ ¥ Rs INR etc) and whitespace
        cleaned = re.sub(r"[^\d,\.\-]", "", raw_str)
        if not cleaned:
            return None

        # Handle European style (1.250,50) vs Standard (1,250.50)
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                # European format: 1.250,50 -> 1250.50
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # Standard format: 1,250.50 -> 1250.50
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")

        try:
            dec = Decimal(cleaned)
            f_val = float(dec)
            if 0.0 <= f_val <= 100000000.0:
                return round(f_val, 2)
        except (InvalidOperation, ValueError):
            pass
        return None

    def _extract_amount_by_label(
        self, label_pattern: str, exclude_terms: Optional[List[str]] = None
    ) -> Tuple[Optional[float], Optional[float], str]:
        """Extracts a monetary amount following a given label on the same line or adjacent next line.
        Supports varied currency symbols/codes ($ € £ ₹ ¥ Rs INR USD EUR GBP CAD AUD SGD AED etc).
        """
        amt_regex = r"(?:[\$€£₹¥]|rs\.?|inr|usd|eur|gbp|cad|aud)?\s*([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)"
        compiled = re.compile(rf"{label_pattern}\s*[:\-]?\s*{amt_regex}", re.IGNORECASE)

        # 1. Search for same line match
        for line in self.lines:
            if exclude_terms:
                lower_line = line.lower()
                if any(term in lower_line for term in exclude_terms):
                    continue

            m = compiled.search(line)
            if m:
                raw_amt = m.group(1).strip()
                val = self._parse_monetary_value(raw_amt)
                if val is not None:
                    confs = self._find_word_confidences_for_text(raw_amt)
                    confidence = ConfidenceScorer.calculate_field_confidence(
                        self.source_type, self.has_ocr, confs, label_match_type="exact", pattern_match_type="strict"
                    )
                    status = ConfidenceScorer.determine_status(val, confidence)
                    return val, confidence, status

        # 2. Search for adjacent next-line match (e.g. Label on line i, Amount on line i+1)
        label_only = re.compile(rf"^{label_pattern}\s*[:\-]?$", re.IGNORECASE)
        for i, line in enumerate(self.lines):
            if exclude_terms:
                lower_line = line.lower()
                if any(term in lower_line for term in exclude_terms):
                    continue

            if label_only.search(line) and i + 1 < len(self.lines):
                next_line = self.lines[i + 1].strip()
                m_next = re.search(rf"^{amt_regex}$", next_line, re.IGNORECASE)
                if m_next:
                    raw_amt = m_next.group(1).strip()
                    val = self._parse_monetary_value(raw_amt)
                    if val is not None:
                        confs = self._find_word_confidences_for_text(raw_amt)
                        confidence = ConfidenceScorer.calculate_field_confidence(
                            self.source_type, self.has_ocr, confs, label_match_type="fuzzy", pattern_match_type="moderate"
                        )
                        status = ConfidenceScorer.determine_status(val, confidence)
                        return val, confidence, status

        # 3. If label was explicitly present but amount could not be parsed:
        if re.search(rf"\b{label_pattern}\b", self.raw_text, re.IGNORECASE):
            return None, 0.20, "needs_review"

        return None, None, "missing"

    def extract_subtotal(self) -> Tuple[Optional[float], Optional[float], str]:
        """Extracts the subtotal amount without fabricating or assuming subtotal == grand total."""
        subtotal_label = r"\b(?:sub\s*total|sub-total|subtotal|base\s+amount|net\s+amount|amount\s+before\s+tax|items\s+total|total\s+net|taxable\s+amount)\b"
        return self._extract_amount_by_label(subtotal_label)

    def extract_tax(self) -> Tuple[Optional[float], Optional[float], str]:
        """Extracts the tax amount (VAT, GST, Sales Tax, CGST+SGST, etc.).
        Distinguishes explicit 0.0 tax from absent tax. Never assumes tax is zero when absent.
        """
        # 1. Check for explicit zero tax declarations (e.g. 'Tax: $0.00', 'VAT (0%): 0', 'Sales Tax: $0')
        curr = r"(?:[\$€£₹¥]|rs\.?|inr|usd|eur)?"
        zero_tax_patterns = [
            rf"\b(?:total\s+tax|tax\s+amount|vat\s+amount|gst\s+amount|sales\s+tax|vat|gst|hst|pst|tax)\b\s*(?:\(.*?\)|@?\s*\d+%)?\s*[:\-]?\s*{curr}\s*(?:0(?:\.00?)?|nil|none|zero)\b",
            rf"\b(?:tax|vat|gst)\s*\(\s*0%\s*\)\s*[:\-]?\s*{curr}\s*(?:0(?:\.00?)?|nil|none|zero)?\b",
        ]
        for pat in zero_tax_patterns:
            for line in self.lines:
                if re.search(pat, line, re.IGNORECASE):
                    confidence = ConfidenceScorer.calculate_field_confidence(
                        self.source_type, self.has_ocr, label_match_type="exact", pattern_match_type="strict"
                    )
                    return 0.0, confidence, "extracted"

        # 2. Look for positive tax amount line
        tax_label = r"\b(?:total\s+tax|tax\s+amount|vat\s+amount|gst\s+amount|sales\s+tax|vat|gst|hst|pst|tax)\b(?:\s*\(.*?\)|@?\s*\d+%)?"
        res = self._extract_amount_by_label(tax_label)
        if res[0] is not None:
            return res

        # 3. Check for CGST + SGST components
        cgst_val = self._extract_amount_by_label(r"\bcgst\b(?:\s*\(.*?\))?")[0]
        sgst_val = self._extract_amount_by_label(r"\bsgst\b(?:\s*\(.*?\))?")[0]
        if cgst_val is not None and sgst_val is not None:
            total_tax = round(cgst_val + sgst_val, 2)
            confidence = ConfidenceScorer.calculate_field_confidence(
                self.source_type, self.has_ocr, label_match_type="exact", pattern_match_type="strict"
            )
            return total_tax, confidence, "extracted"

        # 4. If tax label was detected in text but amount failed to parse
        if res[2] == "needs_review" or re.search(r"\b(?:tax|vat|gst|sales\s+tax)\b", self.raw_text, re.IGNORECASE):
            # Check if tax is mentioned only inside a compound phrase like 'amount before tax'
            cleaned_text = re.sub(r"\b(?:amount\s+before\s+tax|exclusive\s+of\s+tax|tax\s+invoice)\b", "", self.raw_text, flags=re.IGNORECASE)
            if re.search(r"\b(?:tax|vat|gst|sales\s+tax)\b", cleaned_text, re.IGNORECASE):
                return None, 0.20, "needs_review"

        # 5. Genuinely absent
        return None, None, "missing"

    def extract_grand_total(self) -> Tuple[Optional[float], Optional[float], str]:
        """Extracts the grand total (Total Amount, Net Payable, Amount Due, Balance Due, or Total)."""
        # 1. Look for specific grand total labels first
        specific_label = r"\b(?:grand\s+total|total\s+amount|invoice\s+total|net\s+payable|amount\s+due|balance\s+due|total\s+due|total\s+payable|total\s+to\s+pay|payment\s+due|final\s+total)\b"
        res = self._extract_amount_by_label(specific_label)
        if res[0] is not None:
            return res

        # 2. Fallback to standalone 'Total:' excluding lines with 'subtotal', 'tax', 'qty'
        generic_total_label = r"\btotal\b"
        res_generic = self._extract_amount_by_label(generic_total_label, exclude_terms=["sub", "tax", "qty", "quantity"])
        if res_generic[0] is not None:
            return res_generic

        # 3. Fallback for total-only receipt / slip: find bottom prominent monetary amount
        curr = r"(?:[\$€£₹¥]|rs\.?|inr|usd|eur)?"
        amt_regex = r"([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)"
        for line in reversed(self.lines[-5:]):
            m = re.search(rf"{curr}\s*{amt_regex}", line, re.IGNORECASE)
            if m:
                val = self._parse_monetary_value(m.group(1))
                if val is not None and val > 0:
                    confs = self._find_word_confidences_for_text(m.group(1))
                    confidence = ConfidenceScorer.calculate_field_confidence(
                        self.source_type, self.has_ocr, confs, label_match_type="none", pattern_match_type="moderate"
                    )
                    status = ConfidenceScorer.determine_status(val, confidence)
                    return val, confidence, status

        # 4. If total label detected but amount failed
        if res[2] == "needs_review" or res_generic[2] == "needs_review":
            return None, 0.20, "needs_review"

        return None, None, "missing"

    # =========================================================================
    # MASTER FIELD EXTRACTION PIPELINE
    # =========================================================================
    def extract_all(self) -> ExtractedFields:
        """Executes extraction across all 6 fields and returns structured ExtractedFields."""
        # 1. Vendor Name
        v_name, v_conf, v_status = self.extract_vendor_name()
        
        # 2. Invoice Number
        inv_no, inv_conf, inv_status = self.extract_invoice_number()

        # 3. Invoice Date
        inv_date, d_conf, d_status = self.extract_invoice_date()

        # 4. Subtotal
        subtotal, sub_conf, sub_status = self.extract_subtotal()

        # 5. Tax
        tax, tax_conf, tax_status = self.extract_tax()

        # 6. Grand Total
        g_total, gt_conf, gt_status = self.extract_grand_total()

        return ExtractedFields(
            vendor_name=StringField(value=v_name, confidence=v_conf, status=v_status),
            invoice_number=StringField(value=inv_no, confidence=inv_conf, status=inv_status),
            invoice_date=StringField(value=inv_date, confidence=d_conf, status=d_status),
            subtotal=NumericField(value=subtotal, confidence=sub_conf, status=sub_status),
            tax=NumericField(value=tax, confidence=tax_conf, status=tax_status),
            grand_total=NumericField(value=g_total, confidence=gt_conf, status=gt_status),
        )
'''

with open(target_path, "w", encoding="utf-8") as f:
    f.write(extractor_code)
print("Updated field_extractor.py cleanly!")
