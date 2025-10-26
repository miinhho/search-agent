"""
Context management for search workflows.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict
from langchain_core.messages import BaseMessage

from src.agents.context.source_filter import SourceFilterData


class SearchMetadata(TypedDict):
    """Metadata for tracking search execution."""

    created_at: str
    session_id: float


@dataclass
class SearchContext:
    # Core data containers
    messages: list[BaseMessage] = field(default_factory=list)
    filters: SourceFilterData = field(default_factory=SourceFilterData)

    # Metadata
    metadata: SearchMetadata = field(
        default_factory=lambda: {
            "created_at": datetime.now().isoformat(),
            "session_id": datetime.now().timestamp(),
        }
    )
