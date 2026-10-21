from typing import Any, Dict, Union

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.schemas import (
    EvaluationReportResponse,
    EvaluationUnavailableResponse,
)
from backend.app.services.exporter import ReportExporter

router = APIRouter(tags=["Evaluation"])


@router.get(
    "/evaluation",
    response_model=Union[EvaluationReportResponse, EvaluationUnavailableResponse],
    summary="Retrieve the latest evaluation metrics report",
)
def get_evaluation_report():
    """Returns the latest evaluation report containing field-level accuracy and processing metrics.
    If the evaluation pipeline has not yet been executed, returns an explicit 'unavailable' status.
    """
    report = ReportExporter.load_latest_evaluation()
    if not report:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "unavailable",
                "message": "Evaluation report has not been generated yet. Please run 'python evaluation/evaluate.py' to generate metrics.",
            },
        )
    return report
