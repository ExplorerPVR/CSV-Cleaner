"""CSV cleaning utilities and resilience helpers."""

from __future__ import annotations

from functools import wraps
import logging
import time
from typing import Any, Callable

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
