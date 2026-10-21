# Evaluation Pipeline & Held-Out Dataset

This directory contains the held-out benchmarking pipeline for the Multimodal Document Intelligence system.

## 1. Held-Out Dataset Structure

- **Dataset Size**: 32 distinct held-out documents (`evaluation/dataset/`)
- **Document Formats**:
  - **PDF Documents**: 24 documents (digital text, varied layouts, multi-page structures)
  - **Image Documents**: 8 documents (PNG and JPG formats processed via OCR pipeline)
- **Ground Truth**: Manually verified values stored in `evaluation/ground_truth.csv`

## 2. Correctness & Normalization Rules

| Field | Normalization & Matching Rule |
| :--- | :--- |
| **`vendor_name`** | Strips leading/trailing whitespace, converts to lowercase, and checks for normalized string containment or exact match. |
| **`invoice_number`** | Exact string match preserving leading zeros, hyphens, and alphanumeric tokens (case-insensitive). |
| **`invoice_date`** | Standardized to ISO `YYYY-MM-DD`. Ambiguous dates are flagged or kept raw if month/day cannot be conclusively distinguished. |
| **`subtotal`** | Parsed to standard IEEE floating-point numbers rounded to 2 decimal places with $0.05 tolerance. |
| **`tax`** | Parsed to standard numeric float with $0.05 tolerance. Supports single tax lines and summed components (e.g., CGST + SGST). |
| **`grand_total`** | Parsed to standard numeric float with $0.05 tolerance. |

## 3. Accuracy Calculation

Field-level accuracy is computed according to the formula:
```
field_accuracy = (correct_predictions / total_evaluated_documents) * 100
```

Unreadable documents and missing predictions are reported explicitly in the `missing_count` metric and are treated as non-matching in accuracy calculations.

## 4. Execution

To run the evaluation pipeline:
```powershell
python evaluation/evaluate.py
```

Generated outputs:
- `reports/evaluation_report.json`
- `reports/evaluation_report.csv`

These outputs are also exposed to the frontend accuracy dashboard via the `GET /api/evaluation` endpoint.
