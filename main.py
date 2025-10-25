"""
Main entry point for the search agent.

Demonstrates the refactored search agent architecture with proper
separation of concerns and LangChain/LangGraph best practices.
"""

import asyncio
import logging
from dotenv import load_dotenv

from src.workflow import run_search_agent
from src.utils.logger import setup_logger

load_dotenv()
setup_logger()

logger = logging.getLogger(__name__)


async def main():
    """Run the search agent with the refactored workflow architecture."""

    user_query = "What are the latest developments in quantum computing in 2025?"

    print("=" * 70)
    print("Search Agent")
    print("=" * 70)
    print(f"\nUser Query: {user_query}\n")

    try:
        logger.info(f"Starting search for: {user_query}")

        # Run the search agent
        result = await run_search_agent(user_query=user_query, max_attempts=3)

        # Display execution log
        print("─" * 70)
        print("EXECUTION LOG:")
        print("─" * 70)
        for log_entry in result["execution_log"]:
            print(log_entry)

        # Display final answer
        print("\n" + "─" * 70)
        print("FINAL ANSWER:")
        print("─" * 70)
        print(result["final_answer"])

        # Display comprehensive statistics
        print("\n" + "─" * 70)
        print("STATISTICS:")
        print("─" * 70)
        print(f"Attempts: {result['attempts']}")
        print(f"Messages in history: {len(result['messages'])}")

        if result["flagged_sources"]:
            print(f"Flagged sources: {', '.join(result['flagged_sources'])}")
        else:
            print("No sources flagged")

        # Display context statistics
        print("\n" + "─" * 70)
        print("CONTEXT DETAILS:")
        print("─" * 70)
        context_stats = result["context"]
        print(str(context_stats))

    except Exception as e:
        logger.error(f"Error running search agent: {e}")
        print(f"❌ Error running search agent: {e}")
        raise

    print("\n" + "=" * 70)
    print("Workflow complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
