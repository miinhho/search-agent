"""
Optimizer stage of the search agent workflow.

Verifies the LLM's plan and revises it if necessary.
Following LangChain best practices for LLM components.
"""

import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logger = logging.getLogger(__name__)


OPTIMIZER_SYSTEM_PROMPT = """You are an expert plan validator and optimizer. Your task is to evaluate a search plan and determine if it's valid and effective.

Evaluate the plan based on:
1. Clarity: Are the steps clear and actionable?
2. Completeness: Does it address all aspects of the user's query?
3. Feasibility: Are the steps realistic and achievable?
4. Efficiency: Is the plan optimal, or can steps be combined or reordered?
5. Coverage: Will following this plan likely yield comprehensive results?

Response format:
- Start with "VALID" or "INVALID"
- If VALID: Briefly explain why the plan is sound (2-3 sentences)
- If INVALID: List specific issues found and provide a revised plan

Always be constructive and provide improvements where needed."""


class PlanOptimizer:
    """
    Validates and optimizes search plans using LLM.

    Following LangChain best practices:
    - Deterministic validation with low temperature
    - Proper error handling and logging
    - Clear validation criteria
    """

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the PlanOptimizer.

        Args:
            model_name: The Google Generative AI model to use
            temperature: Temperature for deterministic validation (lower is more consistent)
        """
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            streaming=True,
        )
        logger.info(f"PlanOptimizer initialized with model: {model_name}, temp: {0.3}")

    def optimize_plan(
        self,
        user_query: str,
        plan: str,
    ) -> tuple[bool, str]:
        """
        Validate and optimize a plan synchronously.

        Args:
            user_query: The original user query
            plan: The plan to validate

        Returns:
            Tuple of (is_valid, response_text)
        """
        logger.info(f"Optimizing plan for query: {user_query[:100]}...")

        if not plan.strip():
            logger.warning("Empty plan provided for optimization")
            return (
                False,
                "INVALID: Empty plan provided. Please generate a valid plan first.",
            )

        validation_prompt = f"""User Query: {user_query}

Generated Plan:
{plan}

Please validate this plan and provide feedback or improvements."""

        messages = [
            SystemMessage(content=OPTIMIZER_SYSTEM_PROMPT),
            HumanMessage(content=validation_prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else ""

        # Determine validity from response
        is_valid = content.upper().startswith("VALID")

        logger.info(f"Plan optimization complete: valid={is_valid}")
        return is_valid, content


# Export main classes and functions
__all__ = [
    "PlanOptimizer",
]
