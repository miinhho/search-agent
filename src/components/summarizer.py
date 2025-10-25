"""
Summarize stage of the search agent workflow.

Validates the response against user requirements and checks source validity.
"""

import logging
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


SUMMARIZE_SYSTEM_PROMPT = """You are an expert information synthesizer and validator. Your task is to:

1. Analyze the search results provided
2. Create a comprehensive answer to the user's query
3. Validate that the answer addresses the user's intent and requirements
4. Identify and flag potentially unreliable or suspicious sources

Response format:
- Start with "VALID" or "INVALID"
- If VALID: Provide the synthesized answer based on the search results
- If INVALID: Explain what's missing and what needs to be re-searched

When identifying sources, extract domain names from URLs and flag any that appear:
- Outdated or no longer maintained
- Potentially biased or unreliable
- Spam or low-quality content
- Commercial sites pushing products rather than information

Flag sources like: "FLAGGED_SOURCES: domain1.com, domain2.com"
"""


class Summarizer:
    """Synthesizes search results and validates response quality."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """Initialize the Summarizer."""

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.5,
            streaming=True,
        )
        logger.info(f"Summarizer initialized with model: {model_name}, temp: {0.5}")

    def summarize(
        self,
        user_query: str,
        search_results: str,
    ) -> tuple[bool, str, list[str]]:
        """
        Synthesize search results and validate synchronously.

        Args:
            user_query: The original user query
            search_results: The search results from Action stage

        Returns:
            Tuple of (is_valid, response_text, flagged_sources)
        """
        logger.info(f"Starting summarization for query: {user_query[:100]}...")

        if not search_results.strip():
            logger.warning("Empty search results provided")
            return False, "No search results available to summarize.", []

        synthesis_prompt = f"""User Query: {user_query}

Search Results:
{search_results}

Please synthesize these results into a comprehensive answer and validate its quality."""

        messages = [
            SystemMessage(content=SUMMARIZE_SYSTEM_PROMPT),
            HumanMessage(content=synthesis_prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else ""

        # Determine validity from response
        is_valid = content.upper().startswith("VALID")

        # Extract flagged sources
        flagged_sources = self._extract_flagged_sources(content)

        logger.info(
            f"Summarization complete: valid={is_valid}, "
            f"flagged_sources={len(flagged_sources)}, "
            f"content_length={len(content)}"
        )

        return is_valid, content, flagged_sources

    def _extract_flagged_sources(self, response: str) -> list[str]:
        """
        Extract flagged sources from the response.

        Args:
            response: The synthesizer response

        Returns:
            List of flagged domain names
        """
        flagged = []

        # Look for pattern like "FLAGGED_SOURCES: domain1.com, domain2.com"
        match = re.search(r"FLAGGED_SOURCES:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        if match:
            sources_text = match.group(1)
            # Split by comma and clean up
            domains = [s.strip() for s in sources_text.split(",")]
            flagged.extend([d for d in domains if d and d.strip()])

        logger.debug(f"Extracted flagged sources: {flagged}")
        return flagged


__all__ = [
    "Summarizer",
]
