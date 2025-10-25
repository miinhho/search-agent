"""
Validation tracking data structures.
"""

from dataclasses import dataclass


@dataclass
class ValidationData:
    """Simple container for validation tracking."""

    invalid_attempts: int = 0

    def should_retry(self, max_retries: int = 3) -> bool:
        return self.invalid_attempts < max_retries
