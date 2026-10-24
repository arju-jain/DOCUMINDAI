from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

FieldStatus = Literal["extracted", "low_confidence", "missing", "invalid", "needs_review"]
OverallStatus = Literal["valid", "needs_review", "invalid"]


class BaseField(BaseModel):
    value: Optional[Any] = None
    confidence: Optional[float] = None
    status: FieldStatus = "missing"


class StringField(BaseField):
    value: Optional[str] = None


class NumericField(BaseField):
    value: Optional[float] = None


class ExtractedFields(BaseModel):
    vendor_name: StringField = Field(default_factory=StringField)
    invoice_number: StringField = Field(default_factory=StringField)
    invoice_date: StringField = Field(default_factory=StringField)
    subtotal: NumericField = Field(default_factory=NumericField)
    tax: NumericField = Field(default_factory=NumericField)
    grand_total: NumericField = Field(default_factory=NumericField)


class ValidationIssue(BaseModel):
    field: Optional[str] = None
    code: str
    message: str


class ValidationResult(BaseModel):
    overall_status: OverallStatus = "valid"
    issues: List[ValidationIssue] = Field(default_factory=list)


class DocumentProcessResponse(BaseModel):
    document_id: str
    filename: str
    document_type: str = "invoice"
    fields: ExtractedFields
    validation: ValidationResult
    # Additional non-breaking metadata
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    ocr_available: bool = True
    ocr_engine: Optional[str] = None


class FieldAccuracyReport(BaseModel):
    evaluated_count: int
    correct_count: int
    missing_count: int
    accuracy_percentage: float


class EvaluationReportResponse(BaseModel):
    status: str = "completed"
    message: Optional[str] = None
    total_documents: int
    successfully_processed: int
    failed_processing: int
    field_metrics: Dict[str, FieldAccuracyReport]
    overall_accuracy_percentage: float
    normalization_rules: Dict[str, str]
    evaluated_at: Optional[str] = None


class EvaluationUnavailableResponse(BaseModel):
    status: str = "unavailable"
    message: str = "Evaluation report has not been generated yet. Please run evaluation/evaluate.py first."
