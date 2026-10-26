"""CSV cleaning utilities and resilience helpers."""

from __future__ import annotations

from functools import wraps
import logging
from pathlib import Path
import time
from typing import Any, Callable

import pandas as pd

logger = logging.getLogger(__name__)


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
        csv_path = Path(data)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        df = pd.read_csv(csv_path)
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


def save_cleaned_data(df: pd.DataFrame, output_path: str | Path) -> Path:
    """Save cleaned DataFrame to a new CSV file.

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
    df.to_csv(dest, index=False)
    logger.info("Saved %d cleaned rows to %s", len(df), dest)
    return dest


# Semantic aliases for clarity
read_and_clean_reviews = clean_reviews
save_cleaned_reviews = save_cleaned_data


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

