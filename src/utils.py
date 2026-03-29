"""
Utility helpers for data cleaning and formatting.
"""

import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Light cleaning pass:
    - Drop columns that are entirely empty
    - Drop rows that are entirely empty
    - Strip whitespace from string column names
    """
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df.reset_index(drop=True)


def format_number(value: float) -> str:
    """
    Human-readable number formatting.
    1_500_000 → "1.5M", 3_200 → "3,200", 0.0045 → "0.0045"
    """
    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{sign}{abs_val:,.0f}"
    if abs_val < 0.01 and abs_val > 0:
        return f"{sign}{abs_val:.4f}"
    return f"{sign}{abs_val:.2f}"
