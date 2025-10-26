"""
State definitions for search agent workflow.

Defines the core state structure and initialization logic for LangGraph workflows.
"""

from typing import TypedDict
from src.agents.context import SearchContext

from src.utils.validation_status import ValidationStatus


class AgentState(TypedDict):
    """State definition for workflow."""

    # Core workflow data
    user_query: str
    plan: list[str]
    search_results: str
    summary: str
    summary_valid: ValidationStatus

    # Control flow
    attempt: int
    max_attempts: int

    # Results
    final_answer: str
    execution_log: list[str]

    # Context reference
    context: SearchContext


def create_initial_state(user_query: str, max_attempts: int = 3) -> AgentState:
    context = SearchContext()

    return {
        "user_query": user_query,
        "plan": [],
        "search_results": "",
        "summary": "",
        "summary_valid": ValidationStatus.INVALID,
        "attempt": 1,
        "max_attempts": max_attempts,
        "final_answer": "",
        "execution_log": [],
        "context": context,
    }
