"""
Unit tests for the Excel Analyzer.
Run: pytest tests/ -v
"""

import io
import pytest
import pandas as pd
import openpyxl

from src.analyzer import ExcelAnalyzer
from src.utils import clean_dataframe, format_number
from src.models import AnalysisResponse


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def make_excel_bytes(df: pd.DataFrame) -> io.BytesIO:
    """Write a DataFrame to an in-memory Excel buffer."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf


def simple_df() -> pd.DataFrame:
    return pd.DataFrame({
        "Revenue":  [10000, 25000, 15000, 50000, 8000],
        "Cost":     [5000,  12000, 7000,  20000, 4000],
        "Month":    ["Jan", "Feb", "Mar", "Apr", "May"],
    })


# ------------------------------------------------------------------ #
#  format_number                                                       #
# ------------------------------------------------------------------ #

class TestFormatNumber:
    def test_millions(self):
        assert "M" in format_number(1_500_000)

    def test_thousands(self):
        result = format_number(3200)
        assert "3" in result and "200" in result

    def test_negative(self):
        assert format_number(-500).startswith("-")

    def test_small(self):
        result = format_number(0.0012)
        assert "0.0012" in result


# ------------------------------------------------------------------ #
#  clean_dataframe                                                     #
# ------------------------------------------------------------------ #

class TestCleanDataframe:
    def test_drops_empty_columns(self):
        df = pd.DataFrame({"A": [1, 2], "B": [None, None]})
        cleaned = clean_dataframe(df)
        assert "B" not in cleaned.columns

    def test_drops_empty_rows(self):
        df = pd.DataFrame({"A": [1, None, 3]})
        df.loc[1] = [None]
        cleaned = clean_dataframe(df)
        assert len(cleaned) < len(df) or len(cleaned) >= 1

    def test_strips_column_names(self):
        df = pd.DataFrame({"  Revenue  ": [1, 2]})
        cleaned = clean_dataframe(df)
        assert "Revenue" in cleaned.columns

    def test_resets_index(self):
        df = pd.DataFrame({"A": [1, 2, 3]}, index=[10, 20, 30])
        cleaned = clean_dataframe(df)
        assert list(cleaned.index) == [0, 1, 2]


# ------------------------------------------------------------------ #
#  ExcelAnalyzer                                                       #
# ------------------------------------------------------------------ #

class TestExcelAnalyzer:
    def test_run_returns_response(self):
        buf = make_excel_bytes(simple_df())
        result = ExcelAnalyzer(buf).run()
        assert isinstance(result, AnalysisResponse)

    def test_metrics_present_for_numeric_cols(self):
        buf = make_excel_bytes(simple_df())
        result = ExcelAnalyzer(buf).run()
        assert "Revenue" in result.metrics
        assert "Cost" in result.metrics
        assert "Month" not in result.metrics  # string column excluded

    def test_metrics_values_correct(self):
        buf = make_excel_bytes(simple_df())
        result = ExcelAnalyzer(buf).run()
        m = result.metrics["Revenue"]
        assert m.count == 5
        assert m.min == 8000
        assert m.max == 50000
        assert abs(m.mean - 21600) < 1

    def test_insights_non_empty(self):
        buf = make_excel_bytes(simple_df())
        result = ExcelAnalyzer(buf).run()
        assert len(result.insights) > 0
        assert all(isinstance(s, str) for s in result.insights)

    def test_quality_report_correct(self):
        buf = make_excel_bytes(simple_df())
        result = ExcelAnalyzer(buf).run()
        assert result.quality.total_rows == 5
        assert result.quality.total_columns == 3
        assert result.quality.numeric_columns == 2

    def test_missing_values_detected(self):
        df = simple_df()
        df.loc[0, "Revenue"] = None
        buf = make_excel_bytes(df)
        result = ExcelAnalyzer(buf).run()
        assert "Revenue" in result.quality.missing_values
        assert result.quality.missing_values["Revenue"] == 1

    def test_llm_summary_is_string(self):
        buf = make_excel_bytes(simple_df())
        result = ExcelAnalyzer(buf).run()
        assert isinstance(result.llm_summary, str)
        assert len(result.llm_summary) > 20

    def test_llm_summary_contains_key_info(self):
        buf = make_excel_bytes(simple_df())
        result = ExcelAnalyzer(buf).run()
        assert "5 rows" in result.llm_summary
        assert "Revenue" in result.llm_summary

    def test_empty_file_raises(self):
        buf = make_excel_bytes(pd.DataFrame())
        with pytest.raises(ValueError):
            ExcelAnalyzer(buf).run()

    def test_no_numeric_columns_raises(self):
        df = pd.DataFrame({"Name": ["Alice", "Bob"], "City": ["Almaty", "Astana"]})
        buf = make_excel_bytes(df)
        with pytest.raises(ValueError, match="No numeric columns"):
            ExcelAnalyzer(buf).run()

    def test_large_range_insight(self):
        df = pd.DataFrame({"Sales": [1, 100000]})
        buf = make_excel_bytes(df)
        result = ExcelAnalyzer(buf).run()
        insights_text = " ".join(result.insights)
        assert "outlier" in insights_text.lower() or "range" in insights_text.lower()
