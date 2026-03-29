"""
Pydantic models for request / response validation.
FastAPI uses these to auto-generate OpenAPI docs and validate data.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ColumnMetrics(BaseModel):
    """Statistical metrics for a single numeric column."""
    mean: float = Field(..., description="Arithmetic mean")
    median: float = Field(..., description="50th percentile")
    sum: float = Field(..., description="Total sum")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    std: float = Field(..., description="Standard deviation")
    count: int = Field(..., description="Non-null row count")


class DataQuality(BaseModel):
    """Data quality summary for the uploaded file."""
    total_rows: int
    total_columns: int
    numeric_columns: int
    missing_values: dict[str, int] = Field(
        default_factory=dict,
        description="Column → count of missing values",
    )
    dtypes: dict[str, str] = Field(
        default_factory=dict,
        description="Column → pandas dtype string",
    )


class AnalysisResponse(BaseModel):
    """Full analysis result returned by /analyze."""
    filename: Optional[str] = None
    metrics: dict[str, ColumnMetrics] = Field(
        ..., description="Per-column statistical metrics (numeric columns only)"
    )
    insights: list[str] = Field(
        ..., description="Auto-generated human-readable text insights"
    )
    quality: DataQuality = Field(..., description="Data quality report")
    llm_summary: str = Field(
        ...,
        description=(
            "Compact summary string ready to pass to an LLM "
            "(e.g. GPT-4) for deeper analysis"
        ),
    )

    model_config = {"json_schema_extra": {
        "example": {
            "filename": "sales_q1.xlsx",
            "metrics": {
                "Revenue": {
                    "mean": 52300.5,
                    "median": 48000.0,
                    "sum": 1569015.0,
                    "min": 12000.0,
                    "max": 145000.0,
                    "std": 21500.3,
                    "count": 30,
                }
            },
            "insights": [
                "Revenue: mean (52,300) > median (48,000) — right-skewed, possible growth trend.",
                "Revenue: high variability (std=21,500, cv=41%) — check for outliers.",
            ],
            "quality": {
                "total_rows": 30,
                "total_columns": 5,
                "numeric_columns": 3,
                "missing_values": {"Revenue": 0, "Cost": 2},
                "dtypes": {"Revenue": "float64", "Month": "object"},
            },
            "llm_summary": (
                "Dataset has 30 rows and 5 columns. "
                "Numeric columns: Revenue (mean=52300, std=21500), Cost (mean=31000, std=8200). "
                "Missing values: Cost has 2. "
                "Potential insights: Revenue is right-skewed."
            ),
        }
    }}
