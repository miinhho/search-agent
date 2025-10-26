"""
Main entry point for the search agent with streaming capabilities.
"""

import asyncio
import logging
from dotenv import load_dotenv

from src.workflow import run_search_agent_stream
from src.utils.logger import setup_logger

load_dotenv()
setup_logger()

logger = logging.getLogger(__name__)


def display_final_results(result: dict):
    """Display the final results in a formatted way."""

    print("─" * 70)
    print("EXECUTION LOG:")
    print("─" * 70)
    for log_entry in result["execution_log"]:
        print(log_entry)

    print("\n" + "─" * 70)
    print("FINAL ANSWER:")
    print("─" * 70)
    print(result["final_answer"])

    print("\n" + "─" * 70)
    print("STATISTICS:")
    print("─" * 70)
    print(f"Attempts: {result.get('attempts', result.get('attempt', 'N/A'))}")

    flagged_sources = result.get("flagged_sources", [])
    if flagged_sources:
        print(f"Flagged sources: {', '.join(flagged_sources)}")
    else:
        print("No sources flagged")


async def main_streaming():
    """Run the search agent with streaming functionality."""

    user_query = "What are the latest developments in quantum computing in 2025?"

    print("=" * 70)
    print("Search Agent (Real-time Streaming)")
    print("=" * 70)
    print(f"\nUser Query: {user_query}\n")

    try:
        logger.info(f"Starting streaming search for: {user_query}")

        final_state = None
        print("🚀 Starting workflow with real-time updates...\n")

        async for event in run_search_agent_stream(
            user_query=user_query, max_attempts=3
        ):
            for node_name, node_output in event.items():
                if node_name != "__end__":
                    print(f"📊 Node '{node_name}' completed")

                    if "execution_log" in node_output:
                        recent_logs = node_output["execution_log"][-2:]
                        for log_entry in recent_logs:
                            print(f"   {log_entry}")

                    if "attempt" in node_output:
                        print(f"   📈 Attempt: {node_output['attempt']}")

                    if "plan" in node_output and node_output["plan"]:
                        print(
                            f"   📋 Generated {len(node_output['plan'])} search steps"
                        )

                    if (
                        "search_results" in node_output
                        and node_output["search_results"]
                    ):
                        results_length = len(node_output["search_results"])
                        print(f"   🔍 Collected {results_length} characters")

                    print()

                final_state = node_output

        if final_state:
            print("\n" + "=" * 70)
            print("STREAMING WORKFLOW COMPLETED")
            print("=" * 70)
            display_final_results(final_state)

    except KeyboardInterrupt:
        logger.warning("Search agent interrupted by user.")
        print("\n❌ Search agent interrupted by user.")
        return
    except Exception as e:
        logger.error(f"Error running streaming search agent: {e}")
        print(f"❌ Error running streaming search agent: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main_streaming())
