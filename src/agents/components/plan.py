"""
Plan generator for search workflows.
"""

import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.error import NoInputError
from src.agents.components.prompt.plan import PLAN_PROMPT

logger = logging.getLogger(__name__)


class PlanResponse(BaseModel):
    steps: list[str] = Field(description="List of search steps")


class PlanGenerator:
    """Generates search plans using LLM."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
        self.agent = create_agent(model=self.llm, response_format=PlanResponse)

    def generate_plan(self, user_query: str) -> PlanResponse:
        """Generate a search plan for the given query."""

        if not user_query.strip():
            raise NoInputError()

        response = self.agent.invoke(
            {
                "messages": [
                    SystemMessage(content=PLAN_PROMPT),
                    HumanMessage(content=user_query),
                ]
            }
        )
        content: PlanResponse = response["structured_response"]
        return content
