"""
eda.py
Core exploratory-data-analysis calculations, kept separate from plotting so
they can be reused by both the GUI (dataset summary panel) and the report
generator. Covers:
- compute_summary(): mean/median/mode/min/max/std per numeric column
- compute_correlation(): correlation matrix for numeric columns
- detect_outliers(): IQR-based outlier detection per numeric column
- missing_value_report(): null counts per column
"""

import pandas as pd
import numpy as np


def compute_summary(df: pd.DataFrame) -> dict:
    """Descriptive statistics for every numeric column."""
    if df is None or df.empty:
        return {}

    numeric_df = df.select_dtypes(include=[np.number])
    summary = {}

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue

        mode_series = series.mode()
        mode_val = mode_series.iloc[0] if not mode_series.empty else float("nan")

        summary[col] = {
            "mean": round(float(series.mean()), 3),
            "median": round(float(series.median()), 3),
            "mode": round(float(mode_val), 3),
            "min": round(float(series.min()), 3),
            "max": round(float(series.max()), 3),
            "std": round(float(series.std(ddof=1)) if len(series) > 1 else 0.0, 3),
            "skew": round(float(series.skew()), 3) if len(series) > 2 else 0.0,
        }

    return summary


def compute_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation matrix for all numeric columns."""
    if df is None or df.empty:
        return pd.DataFrame()
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return pd.DataFrame()
    return numeric_df.corr(numeric_only=True)


def detect_outliers(df: pd.DataFrame) -> dict:
    """
    IQR-based outlier detection for every numeric column.

    Returns
    -------
    dict: {column_name: {"count": int, "percent": float, "lower": float, "upper": float}}
    """
    if df is None or df.empty:
        return {}

    numeric_df = df.select_dtypes(include=[np.number])
    results = {}

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = series[(series < lower) | (series > upper)]
        results[col] = {
            "count": int(outliers.shape[0]),
            "percent": round(100 * outliers.shape[0] / len(series), 2),
            "lower_bound": round(float(lower), 3),
            "upper_bound": round(float(upper), 3),
        }

    return results


def missing_value_report(df: pd.DataFrame) -> dict:
    """Count and percentage of missing values per column."""
    if df is None or df.empty:
        return {}

    total = len(df)
    report = {}
    for col in df.columns:
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            report[col] = {
                "missing": n_missing,
                "percent": round(100 * n_missing / total, 2),
            }
    return report


def format_summary_text(df: pd.DataFrame) -> str:
    """Render the full numeric summary as a human-readable string."""
    summary = compute_summary(df)
    if not summary:
        return "No numeric columns available to summarize."

    lines = []
    for col, s in summary.items():
        lines.append(f"Column: {col}")
        lines.append(f"  Mean   : {s['mean']}")
        lines.append(f"  Median : {s['median']}")
        lines.append(f"  Mode   : {s['mode']}")
        lines.append(f"  Min    : {s['min']}")
        lines.append(f"  Max    : {s['max']}")
        lines.append(f"  Std    : {s['std']}")
        lines.append(f"  Skew   : {s['skew']}")
        lines.append("")

    return "\n".join(lines)


def format_outlier_text(df: pd.DataFrame) -> str:
    """Render outlier detection results as a human-readable string."""
    outliers = detect_outliers(df)
    if not outliers:
        return "No numeric columns with enough data for outlier detection."

    lines = []
    for col, o in outliers.items():
        lines.append(
            f"{col}: {o['count']} outliers ({o['percent']}%) "
            f"outside [{o['lower_bound']}, {o['upper_bound']}]"
        )
    return "\n".join(lines)
