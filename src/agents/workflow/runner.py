"""
the main entry points for running search agent workflows
"""

import logging
from langfuse.langchain import CallbackHandler

from src.agents.workflow.state import create_initial_state
from src.agents.workflow.graph import create_search_agent_graph

logger = logging.getLogger(__name__)


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
        logger.debug(
            f"Starting streaming search agent for query: {user_query[:100]}..."
        )

        # Create the graph
        graph = create_search_agent_graph()

        # Initialize state
        initial_state = create_initial_state(user_query, max_attempts)

        # Initialize Langfuse callback handler
        langfuse_handler = CallbackHandler()

        # Run the graph with streaming
        async for event in graph.astream(
            initial_state, config={"callbacks": [langfuse_handler]}
        ):
            yield event

    except Exception as e:
        logger.error(f"Error in streaming search agent: {e}")
        raise


__all__ = [
    "run_search_agent_stream",
]
