"""
Summarize stage of the search agent workflow.

Validates the response against user requirements and checks source validity.
"""

import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from src.agents.error import NoSearchResultError
from src.utils import ValidationStatus
from src.agents.components.prompt.summarizer import (
    SUMMARIZE_SYSTEM_PROMPT,
    SYNTHESIS_PROMPT,
)

logger = logging.getLogger(__name__)


class SummarizationResponse(BaseModel):
    status: ValidationStatus
    summary: str = Field(description="Comprehensive answer")
    flagged_sources: list[str] = Field(
        default_factory=list, description="List of unreliable domains"
    )


class Summarizer:
    """Synthesizes search results and validates response quality."""

    def __init__(self):
        llm_model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            temperature=0.5,
        )
        self.agent = create_agent(
            model=llm_model,
            system_prompt=SUMMARIZE_SYSTEM_PROMPT,
            response_format=SummarizationResponse,
        )

    def summarize(
        self,
        user_query: str,
        search_results: str,
    ) -> SummarizationResponse:
        """
        Synthesize search results and validate.

        Args:
            user_query: The original user query
            search_results: The search results from Action stage
        """

        logger.debug(f"Starting summarization for query: {user_query[:100]}...")

        if not search_results.strip():
            logger.warning("Empty search results provided")
            raise NoSearchResultError()

        synthesis_prompt = SYNTHESIS_PROMPT.format(
            user_query=user_query, search_results=search_results
        )
        response = self.agent.invoke({"messages": [HumanMessage(synthesis_prompt)]})
        content: SummarizationResponse = response["structured_response"]

        is_valid = content.status == ValidationStatus.VALID
        flagged_sources = content.flagged_sources

        logger.debug(
            f"Summarization complete: valid={is_valid}, "
            f"flagged_sources={len(flagged_sources)}, "
            f"content_length={len(content.summary)}"
        )

        return content
