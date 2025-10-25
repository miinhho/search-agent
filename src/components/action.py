"""Action executor for search workflows."""

import logging
import re
from ddgs import DDGS

logger = logging.getLogger(__name__)


# TODO : Reduce search latency (currently: 43.637s)
class ActionExecutor:
    """Executes search actions from a validated plan."""

    def __init__(self, max_results: int = 8):
        self.max_results = max_results

    def execute_plan(
        self, plan: str, user_query: str, source_filter: str = ""
    ) -> list[dict]:
        """Execute search plan and return results."""

        search_queries = self._extract_queries(plan, user_query)
        results = []
        print(search_queries)

        for i, query in enumerate(search_queries, 1):
            filtered_query = f"{query} {source_filter}".strip()

            try:
                search_result = self._search(filtered_query)
                results.append(
                    {"task_number": i, "search_query": query, "results": search_result}
                )
            except Exception as e:
                logger.error(f"Search failed for query {i}: {e}")
                results.append(
                    {"task_number": i, "search_query": query, "error": str(e)}
                )

        return results

    def _extract_queries(self, plan: str, user_query: str) -> list[str]:
        """Extract search queries from plan."""

        if not plan.strip():
            return [user_query]

        queries = []
        for line in plan.split("\n"):
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
