"""Unit tests for cleaner and retry utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.cleaner import clean_reviews, retry, save_cleaned_data


# ============================================================================
# Retry Decorator Tests
# ============================================================================

def test_retry_succeeds_after_failing() -> None:
    """Test that retry decorator succeeds after failing on earlier attempts."""
    attempts = 0

    @retry(max_retries=3, delay=0.0)
    def flaky_function() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("Temporary network glitch")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert attempts == 2


def test_retry_gives_up_after_n_tries() -> None:
    """Test that retry decorator gives up after N tries and re-raises the last error."""
    attempts = 0
    max_tries = 3

    @retry(max_retries=max_tries, delay=0.0)
    def always_failing_function() -> None:
        nonlocal attempts
        attempts += 1
        raise ValueError(f"Permanent failure at try {attempts}")

    with pytest.raises(ValueError, match="Permanent failure at try 3"):
        always_failing_function()

    assert attempts == max_tries


def test_retry_specific_exception_filter() -> None:
    """Test that retry only catches specified exceptions and immediately raises others."""
    attempts = 0

    @retry(max_retries=3, delay=0.0, exceptions=(KeyError,))
    def raises_unexpected_error() -> None:
        nonlocal attempts
        attempts += 1
        raise TypeError("Unexpected type error")

    with pytest.raises(TypeError, match="Unexpected type error"):
        raises_unexpected_error()

    # Should fail immediately without retrying
    assert attempts == 1


def test_retry_invalid_max_retries() -> None:
    """Test that configuring retry with less than 1 attempt raises ValueError."""
    with pytest.raises(ValueError, match="max_retries must be at least 1"):
        @retry(max_retries=0)
        def sample_fn() -> None:
            pass


# ============================================================================
# CSV Cleaning and Saving Tests
# ============================================================================

def test_remove_empty_and_whitespace_rows() -> None:
    """Checklist item 1: Empty and whitespace-only rows are removed."""
    raw_df = pd.DataFrame(
        [
            {"review_id": "1", "name": "Alice", "rating": 5, "comment": "Great!"},
            {"review_id": None, "name": None, "rating": None, "comment": None},
            {"review_id": "  ", "name": "   ", "rating": " ", "comment": "\t \n"},
            {"review_id": "2", "name": "Bob", "rating": 4, "comment": "   "},  # Partial whitespace, valid row
            {"review_id": "", "name": "", "rating": "", "comment": ""},
        ]
    )

    cleaned = clean_reviews(raw_df)

    # Completely empty or whitespace-only rows (indices 1, 2, 4) should be removed.
    # Rows 0 (Alice) and 3 (Bob) should be preserved.
    assert len(cleaned) == 2
    assert list(cleaned["review_id"]) == ["1", "2"]
    assert list(cleaned["name"]) == ["Alice", "Bob"]


def test_remove_duplicate_rows() -> None:
    """Checklist item 2: Duplicate rows are removed."""
    raw_df = pd.DataFrame(
        [
            {"review_id": "101", "name": "John Doe", "rating": 5, "comment": "Superb"},
            {"review_id": "102", "name": "Jane Smith", "rating": 4, "comment": "Good"},
            {"review_id": "101", "name": "John Doe", "rating": 5, "comment": "Superb"},  # Exact duplicate
            {"review_id": "102", "name": "Jane Smith", "rating": 4, "comment": "Good"},  # Exact duplicate
            {"review_id": "103", "name": "Emily Clark", "rating": 5, "comment": "Loved it"},
        ]
    )

    cleaned = clean_reviews(raw_df)

    # Only unique rows should remain
    assert len(cleaned) == 3
    assert list(cleaned["review_id"]) == ["101", "102", "103"]


def test_clean_reviews_does_not_mutate_original() -> None:
    """Test that cleaning does not modify the original data and returns a new copy."""
    original_df = pd.DataFrame(
        [
            {"id": "1", "text": "Valid"},
            {"id": "", "text": "   "},
            {"id": "1", "text": "Valid"},
        ]
    )
    original_copy = original_df.copy(deep=True)

    cleaned_df = clean_reviews(original_df)

    # Original DataFrame must remain untouched
    pd.testing.assert_frame_equal(original_df, original_copy)
    assert cleaned_df is not original_df
    assert len(cleaned_df) == 1
    assert cleaned_df.iloc[0]["id"] == "1"


def test_save_cleaned_data(tmp_path: Path) -> None:
    """Test that save_cleaned_data saves the DataFrame correctly to a new CSV file."""
    df = pd.DataFrame(
        [
            {"review_id": "101", "customer_name": "Alice", "rating": 5},
            {"review_id": "102", "customer_name": "Bob", "rating": 4},
        ]
    )
    output_file = tmp_path / "subfolder" / "cleaned_output.csv"

    saved_path = save_cleaned_data(df, output_file)

    assert saved_path.exists()
    reloaded_df = pd.read_csv(saved_path)
    assert len(reloaded_df) == 2
    assert list(reloaded_df["review_id"]) == [101, 102]
    assert list(reloaded_df["customer_name"]) == ["Alice", "Bob"]


def test_clean_reviews_file_not_found() -> None:
    """Test that clean_reviews raises FileNotFoundError when given a non-existent path."""
    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        clean_reviews("non_existent_file.csv")


def test_end_to_end_sample_reviews_cleaning(tmp_path: Path) -> None:
    """End-to-end pipeline test using data/sample_reviews.csv."""
    sample_csv = Path("data/sample_reviews.csv")
    assert sample_csv.exists(), "Sample CSV file must exist at data/sample_reviews.csv"

    raw_df = pd.read_csv(sample_csv)
    # The messy sample has 16 rows (including 4 all-blank rows and 3 duplicates)
    assert len(raw_df) == 16

    cleaned_df = clean_reviews(sample_csv)
    # Cleaned DataFrame should have exactly 9 valid, unique rows
    assert len(cleaned_df) == 9

    # Verify saving works
    out_csv = tmp_path / "cleaned_reviews.csv"
    save_cleaned_data(cleaned_df, out_csv)
    assert out_csv.exists()

    reloaded = pd.read_csv(out_csv)
    assert len(reloaded) == 9
