"""
Action executor for search workflows.
"""

import logging
import asyncio
from dataclasses import dataclass
from ddgs import DDGS


logger = logging.getLogger(__name__)


@dataclass
class SearchInformation:
    title: str
    body: str
    url: str

    def format(self) -> str:
        return f"[{self.title}]({self.url})\n{self.body}"


@dataclass
class SearchResult:
    task_number: int
    search_query: str
    results: list[SearchInformation]

    def result_format(self) -> str | None:
        if not self.results:
            return None

        formatted = f"**Query: {self.search_query}**\n\n"
        for i, info in enumerate(self.results, 1):
            formatted += f"{i}. {info.format()}\n\n"
        return formatted


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
    ) -> list[SearchResult]:
        """Execute search plan and return results."""

        tasks: list[tuple[int, str, str]] = []
        for i, query in enumerate(plan, 1):
            filtered_query = f"{query} {source_filter}".strip()
            tasks.append((i, query, filtered_query))

        async def run_search(
            task_number: int, original_query: str, filtered_query: str
        ) -> SearchResult | None:
            try:
                logger.debug(
                    f"Executing search task {task_number}: {original_query[:50]}..."
                )
                search_result = await asyncio.to_thread(self._search, filtered_query)
                logger.debug(
                    f"Task {task_number} completed: {len(search_result)} characters"
                )
                return SearchResult(
                    task_number=task_number,
                    search_query=original_query,
                    results=search_result,
                )
            except Exception as e:
                logger.error(f"Search failed for query {task_number}: {e}")
                return None

        # Gather all tasks
        results = await asyncio.gather(
            *[
                run_search(task_number, original_query, filtered_query)
                for task_number, original_query, filtered_query in tasks
            ],
            return_exceptions=True,
        )

        # Filter out exceptions and None results
        valid_results = [
            r for r in results if r is not None and isinstance(r, SearchResult)
        ]
        logger.debug(f"Search execution completed: {len(valid_results)} valid results")
        return valid_results

    def _search(self, query: str) -> list[SearchInformation]:
        """Perform search using DDGS."""

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=self.max_results))

            if not results:
                return []

            formatted: list[SearchInformation] = []
            for result in results:
                title = result.get("title", "No title")
                body = result.get("body", "No description")
                url = result.get("href", "No URL")
                formatted.append(SearchInformation(title=title, body=body, url=url))

            return formatted
