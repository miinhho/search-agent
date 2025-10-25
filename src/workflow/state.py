"""
State definitions for search agent workflow.

Defines the core state structure and initialization logic for LangGraph workflows.
"""

from typing import TypedDict
from src.context import SearchContext


class AgentState(TypedDict):
    """State definition for workflow."""

    # Core workflow data
    user_query: str
    plan: str
    plan_valid: bool
    search_results: str
    summary: str
    summary_valid: bool

    # Control flow
    attempt: int
    max_attempts: int

    # Results
    final_answer: str
    execution_log: list[str]

    # Context reference
    context: SearchContext


def create_initial_state(user_query: str, max_attempts: int = 3) -> AgentState:
    """
    Create initial AgentState

    Args:
        user_query: The user's search query
        max_attempts: Maximum retry attempts

    Returns:
        Initialized AgentState
    """
    context = SearchContext()

    return {
        "user_query": user_query,
        "plan": "",
        "plan_valid": False,
        "search_results": "",
        "summary": "",
        "summary_valid": False,
        "attempt": 1,
        "max_attempts": max_attempts,
        "final_answer": "",
        "execution_log": [],
        "context": context,
    }
