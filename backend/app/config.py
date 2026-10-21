import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseModel):
    app_name: str = "Multimodal Document Intelligence"
    version: str = "1.0.0"
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "False").lower() in ("true", "1", "t"))
    
    # Server configuration
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    
    # CORS origins
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://127.0.0.1:8081,http://localhost:8081,http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:5500,http://localhost:5500,http://localhost:5173,http://localhost:3000",
            ).split(",")
            if origin.strip()
        ]
    )
    cors_origin_regex: Optional[str] = Field(
        default_factory=lambda: os.getenv("CORS_ORIGIN_REGEX", None)
    )
    
    # Upload limits
    max_upload_size_bytes: int = Field(
        default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(15 * 1024 * 1024)))
    )
    max_pages: int = Field(default_factory=lambda: int(os.getenv("MAX_PAGES", "15")))
    
    # Extraction and Validation thresholds
    confidence_threshold: float = Field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
    )
    rounding_tolerance: float = Field(
        default_factory=lambda: float(os.getenv("ROUNDING_TOLERANCE", "0.05"))
    )
    
    # OCR Settings
    tesseract_cmd: Optional[str] = Field(default_factory=lambda: os.getenv("TESSERACT_CMD", "").strip() or None)
    tessdata_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("TESSDATA_DIR", str(BASE_DIR / "backend" / "app" / "tessdata"))
        ).resolve()
    )
    ocr_dpi: int = Field(default_factory=lambda: int(os.getenv("OCR_DPI", "150")))
    
    # Report & Evaluation paths
    reports_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))).resolve()
    )
    evaluation_report_json: Path = Field(
        default_factory=lambda: (
            Path(os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))).resolve() / "evaluation_report.json"
        )
    )
    evaluation_report_csv: Path = Field(
        default_factory=lambda: (
            Path(os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))).resolve() / "evaluation_report.csv"
        )
    )
    ground_truth_csv: Path = Field(
        default_factory=lambda: BASE_DIR / "evaluation" / "ground_truth.csv"
    )
    evaluation_dataset_dir: Path = Field(
        default_factory=lambda: BASE_DIR / "evaluation" / "dataset"
    )
    
    # File Signature constants (Magic Bytes)
    magic_signatures: dict = {
        "pdf": b"%PDF-",
        "png": b"\x89PNG\r\n\x1a\n",
        "jpeg": b"\xff\xd8\xff",
    }
    allowed_extensions: tuple = (".pdf", ".png", ".jpg", ".jpeg")


settings = Settings()
