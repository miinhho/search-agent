"""
Graph construction and workflow components for search agent.
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.components import PlanGenerator, ActionExecutor, Summarizer
from src.utils import ValidationStatus
from src.agents.workflow.state import AgentState

logger = logging.getLogger(__name__)


def create_search_agent_graph(max_results: int = 4):
    plan_generator = PlanGenerator()
    action_executor = ActionExecutor(max_results)
    summarizer = Summarizer()

    workflow = StateGraph(AgentState)

    # Node Functions

    def node_generate_plan(state: AgentState) -> AgentState:
        """Generate search plan from user query."""

        try:
            state["execution_log"].append("📋 Generating search plan...")
            context = state["context"]
            user_query = state["user_query"]

            context.messages.append(HumanMessage(user_query))

            plan = plan_generator.generate_plan(user_query)
            state["plan"] = plan.steps

            context.messages.append(AIMessage(f"Generated search plan:\n{plan}"))

            state["execution_log"].append(
                f"✅ Plan generated with {len(plan.steps)} steps"
            )

            logger.debug(f"Plan generated successfully: {plan.steps}")
            return state

        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            state["execution_log"].append(f"❌ Error generating plan: {str(e)}")
            return state

    async def node_execute_search(state: AgentState) -> AgentState:
        """Execute the validated plan to search for information."""

        try:
            state["execution_log"].append(
                f"🔎 Executing search (Attempt {state['attempt']})..."
            )

            # Build search filter from flagged sources
            context = state["context"]
            search_filter = context.filters.search_filter

            # Add filter info to log
            if search_filter:
                state["execution_log"].append(
                    f"   🚫 Using search filter: {search_filter}"
                )

            # Execute search
            results = await action_executor.execute_plan(state["plan"], search_filter)

            # Aggregate results
            search_results = ""
            search_summary: list[str] = []
            successful_searches = 0

            for search_result in results:
                search_content = search_result.result_format()
                task_number = search_result.task_number

                if search_content:
                    search_results += search_content + "\n"
                    successful_searches += 1
                    search_summary.append(f"• Task {task_number}: ✅")
                elif search_content is None:
                    search_summary.append(f"• Task {task_number}: ❌ Error")
                else:
                    search_summary.append(f"• Task {task_number}: ⚠️ No results")

            state["search_results"] = search_results

            # Add detailed execution log
            state["execution_log"].append(
                f"✅ Search completed: {successful_searches}/{len(results)} tasks successful"
            )
            for summary in search_summary:
                state["execution_log"].append(summary)
            state["execution_log"].append(
                f"   📄 Total content: {len(search_results)} characters"
            )

            # Add search execution to message history
            context.messages.append(
                AIMessage(
                    f"Search executed (Attempt {state['attempt']}):\n"
                    + "\n".join(search_summary)
                )
            )

            logger.debug(
                f"Search executed: {len(results)} tasks, {len(search_results)} chars"
            )
            return state

        except Exception as e:
            logger.error(f"Error executing search: {e}")
            state["execution_log"].append(f"❌ Error executing search: {str(e)}")
            state["search_results"] = f"Error occurred during search: {str(e)}"
            return state

    def node_summarize(state: AgentState) -> AgentState:
        """Synthesize search results and validate the response."""

        try:
            state["execution_log"].append("📝 Summarizing results...")
            context = state["context"]

            # Add input info to log
            input_length = len(state["search_results"])
            state["execution_log"].append(
                f"   📊 Processing {input_length} characters of search data"
            )

            summarized_result = summarizer.summarize(
                state["user_query"], state["search_results"]
            )

            is_valid = summarized_result.status == ValidationStatus.VALID
            summary = summarized_result.summary
            flagged = summarized_result.flagged_sources
            state["summary_valid"] = summarized_result.status
            state["summary"] = summary

            # Add summary to message history
            summary_preview = summary[:150] + "..." if len(summary) > 150 else summary
            context.messages.append(AIMessage(f"Summary:\n{summary_preview}"))

            # Update validation status with detailed logging
            if is_valid:
                state["final_answer"] = summary
                state["execution_log"].append("✅ Summary validated successfully")
                state["execution_log"].append(
                    f"   📝 Final answer: {len(summary)} characters"
                )
            else:
                state["execution_log"].append(
                    f"⚠️  Summary validation failed (Status: {summarized_result.status})"
                )
                if flagged:
                    state["execution_log"].append(
                        f"   🚫 Flagged sources: {', '.join(flagged)}"
                    )
                    context.filters.add_flagged_sources(flagged)
                    state["execution_log"].append(
                        "   🔄 Will retry with updated filters"
                    )

            logger.debug(
                f"Summarization complete: valid={is_valid}, flagged={len(flagged)}"
            )
            return state

        except Exception as e:
            logger.error(f"Error summarizing: {e}")
            state["execution_log"].append(f"❌ Error summarizing: {str(e)}")
            state["summary_valid"] = ValidationStatus.INVALID
            state["summary"] = f"Error occurred during summarization: {str(e)}"
            return state

    # Conditional Logic
    def should_retry_summary(state: AgentState) -> Literal["execute_search", "end"]:
        """Decide whether to retry search or end with current best answer."""

        user_query = state["user_query"]
        if state["summary_valid"]:
            return "end"
        elif state["attempt"] < state["max_attempts"]:
            # Check if we have meaningful search results to retry with
            if not state["search_results"].strip():
                logger.warning(
                    f"No search results available on attempt {state['attempt']}, ending workflow"
                )
                state["final_answer"] = (
                    f"Unable to find sufficient information about: {user_query}"
                )
                return "end"
            state["attempt"] += 1
            return "execute_search"
        else:
            # Provide fallback answer if we've exhausted attempts
            if not state["final_answer"].strip():
                state["final_answer"] = (
                    f"Search completed but unable to provide definitive answer for: {user_query}"
                )
            return "end"

    workflow.add_node("generate_plan", node_generate_plan)
    workflow.add_node("execute_search", node_execute_search)
    workflow.add_node("summarize", node_summarize)

    workflow.add_edge(START, "generate_plan")
    workflow.add_edge("generate_plan", "execute_search")
    workflow.add_edge("execute_search", "summarize")

    workflow.add_conditional_edges(
        "summarize",
        should_retry_summary,
        {
            "execute_search": "execute_search",
            "end": END,
        },
    )

    return workflow.compile()


__all__ = [
    "create_search_agent_graph",
]
