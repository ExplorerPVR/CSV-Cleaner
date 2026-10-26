"""Unit tests for cleaner and retry utilities."""

from __future__ import annotations

import pytest

from src.cleaner import retry


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
