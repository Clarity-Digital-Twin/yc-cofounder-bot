"""Error recovery mechanisms for robust API interactions.

Implements retry logic, exponential backoff, and fallback strategies.
"""

from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

from ..application.ports import LoggerPort

T = TypeVar("T")


class RetryWithBackoff:
    """Retry failed operations with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        logger: LoggerPort | None = None,
    ) -> None:
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.logger = logger

    def execute(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> T:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            operation_name: Name for logging
            retryable_exceptions: Exceptions that trigger retry

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0 and self.logger:
                    self.logger.emit(
                        {
                            "event": "retry_attempt",
                            "operation": operation_name,
                            "attempt": attempt,
                            "delay": delay,
                        }
                    )

                result = func()

                if attempt > 0 and self.logger:
                    self.logger.emit(
                        {
                            "event": "retry_success",
                            "operation": operation_name,
                            "attempt": attempt,
                        }
                    )

                return result

            except retryable_exceptions as e:
                last_exception = e

                if self.logger:
                    self.logger.emit(
                        {
                            "event": "operation_failed",
                            "operation": operation_name,
                            "attempt": attempt,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "will_retry": attempt < self.max_retries,
                        }
                    )

                if attempt < self.max_retries:
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    # Final failure
                    if self.logger:
                        self.logger.emit(
                            {
                                "event": "retry_exhausted",
                                "operation": operation_name,
                                "attempts": self.max_retries + 1,
                                "final_error": str(e),
                            }
                        )

        if last_exception:
            raise last_exception
        raise RuntimeError(f"Retry logic failed for {operation_name}")


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        logger: LoggerPort | None = None,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.logger = logger
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False

    def call(self, func: Callable[[], T], operation_name: str = "operation") -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            operation_name: Name for logging

        Returns:
            Function result

        Raises:
            CircuitOpenError if circuit is open
            Original exception if function fails
        """
        # Check if circuit should be reset
        if self.is_open:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.is_open = False
                self.failure_count = 0
                if self.logger:
                    self.logger.emit(
                        {"event": "circuit_reset", "operation": operation_name}
                    )
            else:
                raise CircuitOpenError(
                    f"Circuit breaker is open for {operation_name}. "
                    f"Retry after {self.recovery_timeout}s"
                )

        try:
            result = func()
            # Reset on success
            if self.failure_count > 0:
                self.failure_count = 0
                if self.logger:
                    self.logger.emit(
                        {
                            "event": "circuit_recovery",
                            "operation": operation_name,
                        }
                    )
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                if self.logger:
                    self.logger.emit(
                        {
                            "event": "circuit_opened",
                            "operation": operation_name,
                            "failures": self.failure_count,
                            "error": str(e),
                        }
                    )

            raise


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


def with_fallback(
    primary: Callable[[], T],
    fallback: Callable[[], T],
    logger: LoggerPort | None = None,
    operation_name: str = "operation",
) -> T:
    """Execute primary function with fallback on failure.

    Args:
        primary: Primary function to try
        fallback: Fallback function if primary fails
        logger: Optional logger
        operation_name: Name for logging

    Returns:
        Result from primary or fallback
    """
    try:
        return primary()
    except Exception as e:
        if logger:
            logger.emit(
                {
                    "event": "fallback_triggered",
                    "operation": operation_name,
                    "primary_error": str(e),
                    "error_type": type(e).__name__,
                }
            )
        return fallback()