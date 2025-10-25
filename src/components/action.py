"""
Action executor for search workflows.
"""

import logging
import re
import asyncio
from ddgs import DDGS

from src.utils import get_workers

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes search actions from a validated plan."""

    def __init__(self, max_results: int = 4, max_workers: int | None = None):
        """
        Initialize ActionExecutor.

        Args:
            max_results: Number of search results per query (default: 4)
            max_workers: Number of concurrent searches. If None, auto-calculates
                        based on CPU cores. For I/O-bound network tasks,
                        2x CPU count is optimal.
        """
        self.max_results = max_results

        # Auto-calculate optimal workers if not specified
        self.max_workers = get_workers() if max_workers is None else max_workers

    async def execute_plan(
        self, plan: list[str], user_query: str, source_filter: str = ""
    ) -> list[dict]:
        """Execute search plan and return results in parallel asynchronously."""

        search_queries = self._extract_queries(plan, user_query)
        logger.debug(f"Search Queries: {search_queries}")

        # Prepare search tasks
        tasks: list[tuple[int, str, str]] = []
        for i, query in enumerate(search_queries, 1):
            filtered_query = f"{query} {source_filter}".strip()
            tasks.append((i, query, filtered_query))

        async def run_search(
            task_number: int, original_query: str, filtered_query: str
        ) -> dict:
            try:
                search_result = await asyncio.to_thread(self._search, filtered_query)
                return {
                    "task_number": task_number,
                    "search_query": original_query,
                    "results": search_result,
                }
            except Exception as e:
                logger.error(f"Search failed for query {task_number}: {e}")
                return {
                    "task_number": task_number,
                    "search_query": original_query,
                    "error": str(e),
                }

        # Gather all tasks
        results = await asyncio.gather(
            *[
                run_search(task_number, original_query, filtered_query)
                for task_number, original_query, filtered_query in tasks
            ],
            return_exceptions=True,
        )

        # Filter out exceptions if any
        valid_results = [r for r in results if isinstance(r, dict)]
        return valid_results

    def _extract_queries(self, plan: list[str], user_query: str) -> list[str]:
        """Extract search queries from plan."""
        queries: list[str] = []
        for line in plan:
            match = re.match(r"^\s*\d+[\.\)]\s*(.+)", line.strip())
            if match:
                task = match.group(1).strip()
                if len(task) > 5:
                    queries.append(
                        task if "search" in task.lower() else f"{user_query} {task}"
                    )

        return queries if queries else [user_query]

    def _search(self, query: str) -> str:
        """Perform search using DDGS."""

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=self.max_results))

            if not results:
                return f"No results found for: {query}"

            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                body = result.get("body", "No description")
                url = result.get("href", "No URL")
                formatted.append(f"{i}. {title}\n   {body}\n   URL: {url}")

            return "\n\n".join(formatted)
