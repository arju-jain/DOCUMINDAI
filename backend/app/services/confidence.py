from typing import Any, Dict, List, Optional
import math
from backend.app.config import settings


class ConfidenceScorer:
    """Calculates and aggregates confidence scores for extracted document fields.

    Methodology & Signal Architecture:
    -----------------------------------
    Field confidence represents the system's certainty regarding the extraction accuracy
    of a specific token or value. It combines:
      1. OCR Token Confidence (when available from word-level OCR engines like Tesseract).
      2. Label Proximity Signal (whether the field was found immediately following an exact
         contextual label like "Invoice No:", "Tax:", "Total:").
      3. Pattern Specificity (the strictness of the regex pattern matching the value format).
      4. Source Quality (clean digital PDF stream vs scanned image OCR).

    Limitations:
    ------------
    - Uncalibrated OCR scores: OCR engines estimate character classification confidence,
      not true posterior probability of semantic correctness.
    - Embedded Digital Text: Digital PDF streams do not produce OCR confidence;
      confidence is instead derived from layout and syntactic signals.
    - Word Aggregation: Multi-token fields (e.g., vendor names) aggregate token scores
      via geometric mean to penalize low-confidence outlier words.
    """

    @staticmethod
    def aggregate_word_confidences(word_scores: List[float]) -> Optional[float]:
        """Aggregates multiple word-level confidence scores into a single field score
        using the geometric mean to penalize any severely degraded word token.
        """
        valid_scores = [s for s in word_scores if s is not None and 0.0 <= s <= 1.0]
        if not valid_scores:
            return None

        # Geometric mean: exp(sum(log(x)) / N)
        # Avoid log(0) with small epsilon
        eps = 1e-4
        log_sum = sum(math.log(max(eps, s)) for s in valid_scores)
        geom_mean = math.exp(log_sum / len(valid_scores))
        return round(max(0.0, min(1.0, geom_mean)), 2)

    @staticmethod
    def calculate_field_confidence(
        source_type: str,
        has_ocr: bool,
        matched_word_confidences: Optional[List[float]] = None,
        label_match_type: str = "exact",  # 'exact', 'fuzzy', 'header', 'none'
        pattern_match_type: str = "strict",  # 'strict', 'moderate', 'loose'
    ) -> Optional[float]:
        """Calculates a calibrated confidence score for a field given extraction context."""
        # Baseline confidence depends on digital stream vs OCR
        if not has_ocr and source_type == "pdf":
            base = 0.95
        else:
            base = 0.85

        # Label modifier
        label_weights = {
            "exact": 0.04,     # Preceded by explicit contextual label (e.g. "Invoice Number:")
            "fuzzy": 0.00,     # Label found with small variation
            "header": -0.05,   # Extracted from header area without explicit label (e.g. vendor name)
            "none": -0.15,     # Extracted solely by regex pattern without label
        }
        label_bonus = label_weights.get(label_match_type, 0.0)

        # Pattern modifier
        pattern_weights = {
            "strict": 0.03,    # Standard ISO date, formatted currency with separators
            "moderate": 0.0,   # Standard alphanumeric pattern
            "loose": -0.10,    # Ambiguous numeric string or unstructured text
        }
        pattern_bonus = pattern_weights.get(pattern_match_type, 0.0)

        calculated_score = base + label_bonus + pattern_bonus

        # If we have actual OCR word confidences, blend them with the syntactic score
        if matched_word_confidences:
            ocr_agg = ConfidenceScorer.aggregate_word_confidences(matched_word_confidences)
            if ocr_agg is not None:
                # 70% OCR token confidence, 30% syntactic/label signal so degraded scans are flagged
                calculated_score = 0.70 * ocr_agg + 0.30 * calculated_score

        # Bound to [0.10, 0.99]
        final_score = max(0.10, min(0.99, calculated_score))
        return round(final_score, 2)

    @staticmethod
    def determine_status(value: Any, confidence: Optional[float]) -> str:
        """Determines the initial field extraction status based on extraction presence
        and confidence threshold.
        Validation status (invalid/needs_review) is applied downstream in the validator.
        """
        if value is None:
            return "missing"

        if confidence is not None and confidence < settings.confidence_threshold:
            return "low_confidence"

        return "extracted"
