"""
file_handler.py
Handles all disk I/O for the app:
- load_csv(): read a CSV into a DataFrame with error handling
- save_visualization(): export the currently displayed matplotlib Figure as PNG
- generate_eda_report(): write a text EDA report (summary, correlation,
  outliers, missing values)
"""

from datetime import datetime
import os
import pandas as pd

from src import eda as eda_module


def load_csv(path: str) -> tuple:
    """
    Load a CSV file into a DataFrame.

    Returns
    -------
    (df, error) : tuple[pd.DataFrame | None, str | None]
    """
    if not path:
        return None, "No file path provided."

    if not os.path.exists(path):
        return None, f"File not found: {path}"

    if not path.lower().endswith(".csv"):
        return None, "Please select a valid .csv file."

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return None, "The selected CSV file is empty."
    except pd.errors.ParserError as e:
        return None, f"Could not parse CSV file: {e}"
    except Exception as e:  # noqa: BLE001
        return None, f"Unexpected error while loading CSV: {e}"

    if df.empty:
        return None, "The CSV file contains no rows."

    return df, None


def save_visualization(fig, output_path: str) -> tuple:
    """
    Save a matplotlib Figure to disk as PNG.

    Returns
    -------
    (success, message) : tuple[bool, str]
    """
    if fig is None:
        return False, "No visualization is currently displayed to save."

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    except Exception as e:  # noqa: BLE001
        return False, f"Failed to save visualization: {e}"

    return True, f"Visualization saved to {output_path}"


def generate_eda_report(df: pd.DataFrame, dataset_name: str, output_path: str) -> tuple:
    """
    Write a plain-text EDA report covering dataset shape, columns,
    descriptive statistics, correlation matrix, outliers, and missing values.

    Returns
    -------
    (success, message) : tuple[bool, str]
    """
    if df is None:
        return False, "No dataset is loaded, nothing to report."

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        lines = []
        lines.append("=" * 64)
        lines.append("SEABORN EDA DASHBOARD - EXPLORATORY DATA ANALYSIS REPORT")
        lines.append("=" * 64)
        lines.append(f"Generated   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Dataset     : {dataset_name}")
        lines.append(f"Rows        : {df.shape[0]}")
        lines.append(f"Columns     : {df.shape[1]}")
        lines.append(f"Column names: {', '.join(df.columns.astype(str))}")
        lines.append("-" * 64)

        lines.append("DESCRIPTIVE STATISTICS (numeric columns)")
        lines.append("-" * 64)
        lines.append(eda_module.format_summary_text(df))

        lines.append("-" * 64)
        lines.append("OUTLIER DETECTION (IQR method, 1.5x rule)")
        lines.append("-" * 64)
        lines.append(eda_module.format_outlier_text(df))
        lines.append("")

        lines.append("-" * 64)
        lines.append("MISSING VALUES")
        lines.append("-" * 64)
        missing = eda_module.missing_value_report(df)
        if missing:
            for col, m in missing.items():
                lines.append(f"{col}: {m['missing']} missing ({m['percent']}%)")
        else:
            lines.append("No missing values detected.")
        lines.append("")

        lines.append("-" * 64)
        lines.append("CORRELATION MATRIX (numeric columns)")
        lines.append("-" * 64)
        corr = eda_module.compute_correlation(df)
        if not corr.empty:
            lines.append(corr.round(3).to_string())
        else:
            lines.append("Not enough numeric columns to compute correlation.")
        lines.append("=" * 64)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    except Exception as e:  # noqa: BLE001
        return False, f"Failed to generate EDA report: {e}"

    return True, f"EDA report generated at {output_path}"
