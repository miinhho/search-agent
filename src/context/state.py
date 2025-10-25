"""
Context management for search workflows.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict, Literal

from langchain_core.messages import BaseMessage
from .search_history import SearchHistoryData
from .source_filter import SourceFilterData
from .validation_tracker import ValidationData


class SearchMetadata(TypedDict, total=False):
    """Metadata for tracking search execution."""

    created_at: str
    session_id: float
    last_search: str
    search_results_length: int
    validation_status: Literal["VALID", "INVALID"]
    flagged_sources: list[str]
    completed_at: str
    total_attempts: int
    total_searches: int


@dataclass
class SearchContext:
    """
    Simple search workflow context using dataclasses.

    Direct access to all data without unnecessary method wrappers.
    """

    # Core data containers
    messages: list[BaseMessage] = field(default_factory=list)
    history: SearchHistoryData = field(default_factory=SearchHistoryData)
    filters: SourceFilterData = field(default_factory=SourceFilterData)
    validation: ValidationData = field(default_factory=ValidationData)

    # Metadata
    metadata: SearchMetadata = field(
        default_factory=lambda: {
            "created_at": datetime.now().isoformat(),
            "session_id": datetime.now().timestamp(),
        }
    )

    def add_search(
        self, query: str, results: str, is_valid: bool, attempt: int = 1, plan: str = ""
    ) -> None:
        """Add a search entry to history."""
        self.history.add_entry(
            query=query,
            results=results,
            is_valid=is_valid,
            attempt=attempt,
            plan=plan,
            flagged_sources=self.filters.flagged_sources.copy(),
        )

    def __str__(self) -> str:
        """String representation."""
        return (
            f"SearchContext("
            f"messages={len(self.messages)}, "
            f"searches={len(self.history.entries)}, "
            f"flagged={len(self.filters.flagged_sources)}, "
            f"invalid_attempts={self.validation.invalid_attempts}"
            f")"
        )
