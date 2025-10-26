"""
Action executor for search workflows.
"""

import logging
import asyncio
from ddgs import DDGS


logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes search actions from a validated plan."""

    def __init__(self, max_results: int = 4):
        """
        Initialize ActionExecutor.

        Args:
            max_results: Number of search results per query (default: 4)
        """
        self.max_results = max_results

    async def execute_plan(
        self, plan: list[str], source_filter: str = ""
    ) -> list[dict]:
        """Execute search plan and return results in parallel asynchronously."""

        tasks: list[tuple[int, str, str]] = []
        for i, query in enumerate(plan, 1):
            filtered_query = f"{query} {source_filter}".strip()
            tasks.append((i, query, filtered_query))

        logger.info(f"Starting parallel execution of {len(tasks)} search tasks")

        async def run_search(
            task_number: int, original_query: str, filtered_query: str
        ) -> dict:
            try:
                logger.debug(
                    f"Executing search task {task_number}: {original_query[:50]}..."
                )
                search_result = await asyncio.to_thread(self._search, filtered_query)
                logger.debug(
                    f"Task {task_number} completed: {len(search_result)} characters"
                )
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
        logger.info(f"Search execution completed: {len(valid_results)} valid results")
        return valid_results

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
