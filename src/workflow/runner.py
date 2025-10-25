"""
the main entry points for running search agent workflows
"""

import logging
from typing import Any
from langfuse.langchain import CallbackHandler


from .state import create_initial_state, SearchContext
from .graph import create_search_agent_graph

logger = logging.getLogger(__name__)


async def run_search_agent(
    user_query: str,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """
    Run the search agent with clean workflow architecture.

    Args:
        user_query: The user's information request
        max_attempts: Maximum number of retry attempts

    Returns:
        Dictionary containing final answer and complete execution context
    """
    try:
        logger.info(f"Starting search agent for query: {user_query[:100]}...")

        # Create the graph
        graph = create_search_agent_graph()

        # Initialize state
        initial_state = create_initial_state(
            user_query=user_query, max_attempts=max_attempts
        )

        # Initialize the Langfuse callback handler
        langfuse_handler = CallbackHandler()

        # Run the graph with Langfuse observability
        final_state = await graph.ainvoke(
            initial_state, config={"callbacks": [langfuse_handler]}
        )

        # Extract context for return
        ctx: SearchContext = final_state["context"]

        result = {
            "query": user_query,
            "final_answer": final_state["final_answer"],
            "execution_log": final_state["execution_log"],
            "attempts": final_state["attempt"],
            # Complete context information
            "context": ctx,
            "messages": ctx.messages,
            "search_history": ctx.history.entries,
            "flagged_sources": ctx.filters.flagged_sources,
            "metadata": ctx.metadata,
            "invalid_attempts": ctx.validation.invalid_attempts,
        }

        logger.info(f"Search agent completed: {final_state['attempt']} attempts")
        return result

    except Exception as e:
        logger.error(f"Error running search agent: {e}")
        raise


async def run_search_agent_stream(user_query: str, max_attempts: int = 3):
    """
    Run the search agent with streaming execution events.

    Args:
        user_query: The user's information request
        max_attempts: Maximum number of retry attempts

    Yields:
        Execution events with updated state
    """
    try:
        logger.info(f"Starting streaming search agent for query: {user_query[:100]}...")

        # Create the graph
        graph = create_search_agent_graph()

        # Initialize state
        initial_state = create_initial_state(
            user_query=user_query, max_attempts=max_attempts
        )

        # Run the graph with streaming
        async for event in graph.astream(initial_state):
            yield event

    except Exception as e:
        logger.error(f"Error in streaming search agent: {e}")
        raise


__all__ = [
    "run_search_agent",
    "run_search_agent_stream",
]
