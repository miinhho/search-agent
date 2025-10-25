"""
Search history data structures.
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import TypedDict


class SearchHistoryEntry(TypedDict):
    """Single search history entry."""

    attempt: int
    query: str
    plan: str
    results: str
    is_valid: bool
    flagged_sources: list[str]
    timestamp: str


@dataclass
class SearchHistoryData:
    """Simple container for search history."""

    entries: list[SearchHistoryEntry] = field(default_factory=list)

    def add_entry(
        self,
        query: str,
        results: str,
        is_valid: bool,
        attempt: int = 1,
        plan: str = "",
        flagged_sources: list[str] | None = None,
    ) -> None:
        """Add a search entry."""

        entry: SearchHistoryEntry = {
            "attempt": attempt,
            "query": query,
            "plan": plan,
            "results": results[:500] if len(results) > 500 else results,
            "is_valid": is_valid,
            "flagged_sources": flagged_sources or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.entries.append(entry)

    @property
    def valid_entries(self) -> list[SearchHistoryEntry]:
        """Get valid search entries."""

        return [e for e in self.entries if e["is_valid"]]

    @property
    def success_rate(self) -> float:
        return len(self.valid_entries) / len(self.entries) if self.entries else 0.0
