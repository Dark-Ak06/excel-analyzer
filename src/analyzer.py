"""
ExcelAnalyzer — core analytics engine.

Pipeline:
    1. Read Excel → DataFrame
    2. Clean data (drop fully-empty rows/cols)
    3. Compute per-column metrics
    4. Generate text insights (rule-based)
    5. Build LLM-ready summary
    6. Return AnalysisResponse
"""

from __future__ import annotations

import io
import pandas as pd

from .models import AnalysisResponse, ColumnMetrics, DataQuality
from .utils import clean_dataframe, format_number


class ExcelAnalyzer:
    """
    Reads an Excel file and produces a structured analysis.

    Parameters
    ----------
    source : str | bytes | io.BytesIO
        Path to the file, raw bytes, or a BytesIO buffer.
    sheet_name : str | int, optional
        Which sheet to analyze. Defaults to the first sheet (0).
    """

    def __init__(self, source: str | bytes | io.BytesIO, sheet_name: int | str = 0):
        self._source = source
        self._sheet_name = sheet_name
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self) -> AnalysisResponse:
        """Execute the full analysis pipeline and return the result."""
        self._df = self._load()
        self._df = clean_dataframe(self._df)

        numeric = self._df.select_dtypes(include="number")
        if numeric.empty:
            raise ValueError("No numeric columns found in the uploaded file.")

        metrics = self._compute_metrics(numeric)
        insights = self._generate_insights(numeric, metrics)
        quality = self._build_quality_report()
        llm_summary = self._build_llm_summary(metrics, quality)

        return AnalysisResponse(
            metrics=metrics,
            insights=insights,
            quality=quality,
            llm_summary=llm_summary,
        )

    # ------------------------------------------------------------------
    # Private — pipeline steps
    # ------------------------------------------------------------------

    def _load(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(self._source, sheet_name=self._sheet_name)
        except Exception as exc:
            raise ValueError(f"Could not read Excel file: {exc}") from exc
        if df.empty:
            raise ValueError("The Excel sheet is empty.")
        return df

    def _compute_metrics(self, numeric: pd.DataFrame) -> dict[str, ColumnMetrics]:
        result: dict[str, ColumnMetrics] = {}
        for col in numeric.columns:
            s = numeric[col].dropna()
            if s.empty:
                continue
            result[str(col)] = ColumnMetrics(
                mean=round(float(s.mean()), 4),
                median=round(float(s.median()), 4),
                sum=round(float(s.sum()), 4),
                min=round(float(s.min()), 4),
                max=round(float(s.max()), 4),
                std=round(float(s.std()), 4) if len(s) > 1 else 0.0,
                count=int(s.count()),
            )
        return result

    def _generate_insights(
        self,
        numeric: pd.DataFrame,
        metrics: dict[str, ColumnMetrics],
    ) -> list[str]:
        insights: list[str] = []

        for col, m in metrics.items():
            # Trend direction from skew (mean vs median)
            if m.mean > m.median * 1.05:
                trend = f"mean ({format_number(m.mean)}) > median ({format_number(m.median)}) — right-skewed, possible growth trend."
            elif m.mean < m.median * 0.95:
                trend = f"mean ({format_number(m.mean)}) < median ({format_number(m.median)}) — left-skewed, possible decline."
            else:
                trend = f"mean ≈ median ({format_number(m.mean)}) — distribution is symmetric, stable pattern."
            insights.append(f"{col}: {trend}")

            # Variability
            if m.mean != 0:
                cv = abs(m.std / m.mean)
                if cv > 0.5:
                    insights.append(
                        f"{col}: high variability (cv={cv:.0%}) — consider investigating outliers."
                    )

            # Missing values
            missing = int(self._df[col].isna().sum()) if col in self._df.columns else 0
            if missing > 0:
                pct = missing / len(self._df) * 100
                insights.append(
                    f"{col}: {missing} missing value(s) ({pct:.1f}%) — imputation may be needed."
                )

            # Range check
            if m.max > 0 and (m.max / max(m.min, 0.001)) > 100:
                insights.append(
                    f"{col}: large range (min={format_number(m.min)}, max={format_number(m.max)}) — outliers likely."
                )

        return insights

    def _build_quality_report(self) -> DataQuality:
        df = self._df
        return DataQuality(
            total_rows=len(df),
            total_columns=len(df.columns),
            numeric_columns=len(df.select_dtypes(include="number").columns),
            missing_values={
                str(col): int(df[col].isna().sum())
                for col in df.columns
                if df[col].isna().sum() > 0
            },
            dtypes={str(col): str(df[col].dtype) for col in df.columns},
        )

    def _build_llm_summary(
        self,
        metrics: dict[str, ColumnMetrics],
        quality: DataQuality,
    ) -> str:
        """
        Produce a compact, information-dense string that can be prepended
        to an LLM prompt for deeper analysis.

        Example usage with OpenAI:
            prompt = f"{summary}\\n\\nPlease provide a business analysis."
            response = openai.chat.completions.create(...)
        """
        parts = [
            f"Dataset: {quality.total_rows} rows, {quality.total_columns} columns.",
            f"Numeric columns: {quality.numeric_columns}.",
        ]

        col_summaries = []
        for col, m in metrics.items():
            col_summaries.append(
                f"{col} (mean={format_number(m.mean)}, std={format_number(m.std)}, "
                f"min={format_number(m.min)}, max={format_number(m.max)})"
            )
        if col_summaries:
            parts.append("Metrics — " + "; ".join(col_summaries) + ".")

        if quality.missing_values:
            mv = ", ".join(f"{c}: {n}" for c, n in quality.missing_values.items())
            parts.append(f"Missing values — {mv}.")

        return " ".join(parts)
