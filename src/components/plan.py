"""Plan generator for search workflows."""

import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

PLAN_PROMPT = """Create a numbered search plan to answer the user's question. 
Each step should be a specific search task.

Format: 
1. [search task]
2. [search task]
..."""


class PlanGenerator:
    """Generates search plans using LLM."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

    def generate_plan(self, user_query: str) -> str:
        """Generate a search plan for the given query."""

        if not user_query.strip():
            return "1. Search for general information"

        messages = [
            SystemMessage(content=PLAN_PROMPT),
            HumanMessage(content=user_query),
        ]

        response = self.llm.invoke(messages)
        content = response.content
        return str(content) if content else "1. Search for information"
