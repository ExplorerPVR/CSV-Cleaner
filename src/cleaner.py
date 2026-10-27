"""CSV cleaning utilities, resilience helpers, and audit reporting engine."""

from __future__ import annotations

from functools import wraps
from io import BytesIO
import logging
from pathlib import Path
import re
import time
from typing import Any, Callable

import pandas as pd
from pydantic import ValidationError

from src.models import CleaningOptions, CleaningStats, ReviewRowModel

logger = logging.getLogger(__name__)


# ============================================================================
# Retry Decorator (Resilience)
# ============================================================================

def retry(
    func_or_retries: Any = None,
    *,
    max_retries: int = 3,
    delay: float = 0.0,
    backoff: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Any:
    """A retry decorator that re-runs a function up to N times when it fails,
    then raises the last error.

    Can be used as:
    - `@retry`: default 3 retries, no delay.
    - `@retry(3)`: 3 retries, positional argument.
    - `@retry(max_retries=5, delay=0.1, backoff=2.0, exceptions=(IOError,))`

    Parameters
    ----------
    func_or_retries : Callable | int | None
        Target function when used as bare decorator `@retry`, or integer retry count
        when used as `@retry(N)`.
    max_retries : int
        Maximum number of attempts (must be at least 1).
    delay : float
        Initial delay (in seconds) between retry attempts.
    backoff : float
        Multiplier applied to the delay after each retry.
    exceptions : tuple of Exception types
        Tuple of exception types to intercept and retry. Defaults to `(Exception,)`.

    Returns
    -------
    Callable
        Decorated function.
    """
    if isinstance(func_or_retries, int):
        effective_retries = func_or_retries
        target_func = None
    elif callable(func_or_retries):
        effective_retries = max_retries
        target_func = func_or_retries
    else:
        effective_retries = max_retries
        target_func = None

    if effective_retries < 1:
        raise ValueError(f"max_retries must be at least 1, got {effective_retries}.")

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Exception | None = None

            for attempt in range(1, effective_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    logger.warning(
                        "Attempt %d/%d for '%s' failed with error: %s",
                        attempt,
                        effective_retries,
                        fn.__name__,
                        exc,
                    )
                    if attempt == effective_retries:
                        raise
                    if current_delay > 0:
                        time.sleep(current_delay)
                        current_delay *= backoff

            if last_exception is not None:
                raise last_exception

        return wrapper

    if target_func is not None:
        return decorator(target_func)
    return decorator


# ============================================================================
# Core Assignment CSV Cleaning & Saving Functions
# ============================================================================

@retry(max_retries=3, delay=0.05, exceptions=(OSError, IOError))
def read_csv_safely(file_path: str | Path) -> pd.DataFrame:
    """Read a CSV file with automatic retry resilience against transient file locks."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)


def clean_reviews(data: str | Path | pd.DataFrame) -> pd.DataFrame:
    """Read a CSV of customer reviews and return a cleaned copy.

    Cleaning rules:
    - Remove rows where every field is empty or only spaces.
    - Remove exact duplicate rows.
    - Do not change original data; returns a new copy.

    Parameters
    ----------
    data : str | Path | pd.DataFrame
        Path to CSV file or DataFrame of customer reviews.

    Returns
    -------
    pd.DataFrame
        Cleaned customer reviews DataFrame with reset index.
    """
    if isinstance(data, (str, Path)):
        df = read_csv_safely(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError("Input data must be a file path (str, Path) or a pandas DataFrame.")

    def _is_empty_or_whitespace(val: Any) -> bool:
        if pd.isna(val):
            return True
        if isinstance(val, str) and val.strip() == "":
            return True
        return False

    empty_cell_mask = df.map(_is_empty_or_whitespace)
    all_empty_row_mask = empty_cell_mask.all(axis=1)

    # Remove rows where every field is empty or only spaces
    cleaned_df = df.loc[~all_empty_row_mask].copy()

    # Remove exact duplicate rows
    cleaned_df = cleaned_df.drop_duplicates()

    # Reset index and return new copy
    cleaned_df = cleaned_df.reset_index(drop=True)
    return cleaned_df


@retry(max_retries=3, delay=0.05, exceptions=(OSError, IOError))
def save_cleaned_data(df: pd.DataFrame, output_path: str | Path) -> Path:
    """Save cleaned DataFrame to a new CSV file with retry resilience.

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned customer reviews DataFrame.
    output_path : str | Path
        Destination path for the new CSV file.

    Returns
    -------
    Path
        Path to the saved CSV file.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}")

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False, encoding="utf-8")
    logger.info("Saved %d cleaned rows to %s", len(df), dest)
    return dest


# Semantic aliases for assignment specification
read_and_clean_reviews = clean_reviews
save_cleaned_reviews = save_cleaned_data


# ============================================================================
# Advanced Pipeline & Audit Engine (Web & Pydantic Integration)
# ============================================================================

def audit_cleaning(
    dataframe: pd.DataFrame,
    options: CleaningOptions | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, CleaningStats]:
    """Execute deep cleaning with step-by-step auditing and Pydantic validation.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, CleaningStats]
        - cleaned_df: Sanitized records with reset index.
        - removed_df: Audit table of all removed rows with 'removal_reason'.
        - stats: Statistical summary metrics and quality score.
    """
    if options is None:
        options = CleaningOptions()

    total_orig = len(dataframe)
    working = dataframe.copy()
    removal_map: dict[int, str] = {}

    def _cell_is_blank(v: Any) -> bool:
        if pd.isna(v):
            return True
        if isinstance(v, str) and v.strip() == "":
            return True
        return False

    # 1. Identify completely empty / whitespace-only rows
    if options.remove_empty_rows:
        blank_mask = working.map(_cell_is_blank).all(axis=1)
        for idx in working[blank_mask].index:
            removal_map[idx] = "Completely empty or whitespace-only row"

    # 2. Check required column constraint
    if options.required_column and options.required_column in working.columns:
        req_col = options.required_column
        req_missing = working[req_col].map(_cell_is_blank)
        for idx in working[req_missing].index:
            if idx not in removal_map:
                removal_map[idx] = f"Missing required value in column: '{req_col}'"

    # 3. Identify duplicate rows (evaluated among non-empty rows)
    if options.remove_duplicates:
        candidate_indices = [i for i in working.index if i not in removal_map]
        subset = options.key_columns if options.key_columns else None
        candidates = working.loc[candidate_indices]
        dup_mask = candidates.duplicated(subset=subset, keep="first")
        for idx in candidates[dup_mask].index:
            scope = f"in keys [{', '.join(subset)}]" if subset else "across all columns"
            removal_map[idx] = f"Exact duplicate record ({scope})"

    # 4. Optional Text-level Sanitization on remaining rows
    active_indices = [i for i in working.index if i not in removal_map]
    str_cols = working.select_dtypes(include=["object", "string"]).columns

    for col in str_cols:
        series = working.loc[active_indices, col]
        if options.strip_html:
            series = series.apply(
                lambda x: re.sub(r"<[^>]+>", "", str(x)) if pd.notna(x) else x
            )
        if options.collapse_spaces:
            series = series.apply(
                lambda x: re.sub(r"\s+", " ", str(x)).strip() if pd.notna(x) else x
            )
        elif options.trim_whitespace:
            series = series.apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        working.loc[active_indices, col] = series

    # 5. Optional Pydantic Schema Validation
    if options.validate_with_pydantic:
        col_names = {c.lower().replace(" ", "_"): c for c in working.columns}

        # Check if dataset has customer review-like columns
        id_col = col_names.get("review_id") or col_names.get("id")
        name_col = col_names.get("customer_name") or col_names.get("name") or col_names.get("customer")
        rating_col = col_names.get("rating") or col_names.get("stars") or col_names.get("score")
        text_col = col_names.get("review_text") or col_names.get("comment") or col_names.get("review") or col_names.get("text")
        date_col = col_names.get("review_date") or col_names.get("date")

        for idx in active_indices:
            row_dict = {
                "review_id": working.at[idx, id_col] if id_col else None,
                "customer_name": working.at[idx, name_col] if name_col else None,
                "rating": working.at[idx, rating_col] if rating_col else None,
                "review_text": working.at[idx, text_col] if text_col else None,
                "review_date": working.at[idx, date_col] if date_col else None,
            }

            try:
                # Validate with Pydantic
                ReviewRowModel.model_validate(row_dict)
            except ValidationError as err:
                error_messages = [e["msg"] for e in err.errors()]
                summary_err = "; ".join(error_messages)
                if options.enforce_rating_bounds and "Rating" in summary_err:
                    removal_map[idx] = f"Pydantic Validation Error: {summary_err}"
                elif "completely empty" in summary_err:
                    removal_map[idx] = "Pydantic Schema: Row has no usable fields"

    # Separate Cleaned and Removed sets
    removed_indices = sorted(removal_map.keys())
    cleaned_indices = [i for i in working.index if i not in removal_map]

    cleaned_df = working.loc[cleaned_indices].copy().reset_index(drop=True)

    if removed_indices:
        removed_df = dataframe.loc[removed_indices].copy()
        removed_df.insert(0, "removal_reason", [removal_map[i] for i in removed_indices])
        removed_df = removed_df.reset_index(drop=True)
    else:
        removed_df = dataframe.iloc[0:0].copy()
        removed_df.insert(0, "removal_reason", [])

    # Calculate statistics
    total_clean = len(cleaned_df)
    total_removed = len(removed_indices)
    retention_rate = (total_clean / total_orig * 100.0) if total_orig > 0 else 100.0
    quality_score = max(0.0, min(100.0, retention_rate))

    removal_breakdown: dict[str, int] = {}
    if not removed_df.empty:
        for reason, count in removed_df["removal_reason"].value_counts().items():
            removal_breakdown[str(reason)] = int(count)

    null_counts: dict[str, int] = {
        col: int(cleaned_df[col].isna().sum()) for col in cleaned_df.columns
    }

    stats = CleaningStats(
        original_rows=total_orig,
        cleaned_rows=total_clean,
        removed_rows=total_removed,
        retention_rate=round(retention_rate, 2),
        data_quality_score=round(quality_score, 1),
        removal_breakdown=removal_breakdown,
        column_null_counts=null_counts,
    )

    return cleaned_df, removed_df, stats


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame as UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_json_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame as indented UTF-8 JSON bytes."""
    return df.to_json(orient="records", indent=2, force_ascii=False).encode("utf-8")


def generate_markdown_audit_report(stats: CleaningStats, filename: str = "dataset.csv") -> str:
    """Generate a formatted markdown data quality audit report."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    breakdown_lines = (
        "\n".join(f"- **{reason}**: `{count}` row(s)" for reason, count in stats.removal_breakdown.items())
        if stats.removal_breakdown
        else "- *No records removed (all rows satisfied quality constraints).*"
    )

    null_lines = "\n".join(
        f"| `{col}` | {count} |" for col, count in stats.column_null_counts.items()
    )

    return f"""# 🛡️ Data Quality & Cleaning Audit Report

**Processed File:** `{filename}`  
**Audit Timestamp:** `{now_str}`  
**Pipeline Engine:** `CSV-Cleaner Pro with Pydantic Validation`  

---

## 1. Executive Summary

| Metric | Value |
| :--- | :--- |
| **Initial Records** | **{stats.original_rows:,}** |
| **Clean Records Retained** | **{stats.cleaned_rows:,}** |
| **Purged Records** | **{stats.removed_rows:,}** |
| **Dataset Retention Rate** | **{stats.retention_rate}%** |
| **Overall Quality Score** | **{stats.data_quality_score} / 100** |

---

## 2. Removal Breakdown & Reasoning

{breakdown_lines}

---

## 3. Clean Dataset Column Null Profile

| Column Name | Remaining Nulls |
| :--- | :--- |
{null_lines}

---
*Report generated automatically by CSV-Cleaner Studio.*
"""


if __name__ == "__main__":
    import sys

    input_file = Path("data/sample_reviews.csv")
    output_file = Path("data/cleaned_reviews.csv")

    if not input_file.exists():
        print(f"Error: Sample data file not found at {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"--> Reading and cleaning reviews from: {input_file}")
    cleaned = clean_reviews(input_file)
    saved_path = save_cleaned_data(cleaned, output_file)
    print(f"--> Success! {len(cleaned)} cleaned rows written to: {saved_path}")
