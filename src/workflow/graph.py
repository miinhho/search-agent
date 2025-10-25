"""
Graph construction and workflow components for search agent.
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage

from src.components import PlanGenerator, PlanOptimizer, ActionExecutor, Summarizer
from .state import AgentState

logger = logging.getLogger(__name__)


def create_search_agent_graph(max_results: int = 8):
    """Create the search agent workflow graph."""

    plan_generator = PlanGenerator()
    plan_optimizer = PlanOptimizer()
    action_executor = ActionExecutor(max_results)
    summarizer = Summarizer()

    workflow = StateGraph(AgentState)

    # Node Functions

    def node_generate_plan(state: AgentState) -> AgentState:
        """Generate search plan from user query."""
        try:
            state["execution_log"].append("📋 Generating search plan...")
            context = state["context"]

            context.messages.append(HumanMessage(state["user_query"]))

            plan = plan_generator.generate_plan(state["user_query"])
            state["plan"] = plan

            context.messages.append(AIMessage(f"Generated search plan:\n{plan}"))

            logger.info(f"Plan generated successfully: {len(plan)} characters")
            return state

        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            state["execution_log"].append(f"❌ Error generating plan: {str(e)}")
            state["plan"] = state["user_query"]  # Fallback to user query
            return state

    def node_optimize_plan(state: AgentState) -> AgentState:
        """Validate and optimize the generated plan."""
        try:
            state["execution_log"].append("🔍 Optimizing plan...")
            context = state["context"]

            is_valid, feedback = plan_optimizer.optimize_plan(
                state["user_query"], state["plan"]
            )
            state["plan_valid"] = is_valid

            # Add validation to message history
            status = "✅ VALID" if is_valid else "❌ INVALID"
            context.messages.append(AIMessage(f"Plan validation: {status}\n{feedback}"))

            if not is_valid:
                state["execution_log"].append("⚠️  Plan needs optimization")
            else:
                state["execution_log"].append("✅ Plan validated successfully")

            logger.info(f"Plan optimization complete: valid={is_valid}")
            return state

        except Exception as e:
            logger.error(f"Error optimizing plan: {e}")
            state["execution_log"].append(f"❌ Error optimizing plan: {str(e)}")
            state["plan_valid"] = True
            return state

    def node_execute_search(state: AgentState) -> AgentState:
        """Execute the validated plan to search for information."""
        try:
            state["execution_log"].append(
                f"🔎 Executing search (Attempt {state['attempt']})..."
            )
            context = state["context"]

            # Build search filter from flagged sources
            search_filter = context.filters.search_filter

            # Execute search
            results = action_executor.execute_plan(
                state["plan"], state["user_query"], search_filter
            )

            # Aggregate results
            search_results = ""
            search_summary: list[str] = []
            for result in results:
                result_content = result.get("results", "")
                query_preview = result["search_query"][:100]

                if result_content and str(result_content).strip():
                    search_results += str(result_content) + "\n"
                    search_summary.append(
                        f"• Task {result['task_number']}: {query_preview}... ✅"
                    )
                elif result.get("error"):
                    search_summary.append(
                        f"• Task {result['task_number']}: {query_preview}... ❌ Error"
                    )
                else:
                    search_summary.append(
                        f"• Task {result['task_number']}: {query_preview}... ⚠️ No results"
                    )

            state["search_results"] = search_results

            # Add search execution to message history
            context.messages.append(
                AIMessage(
                    f"Search executed (Attempt {state['attempt']}):\n"
                    + "\n".join(search_summary)
                )
            )

            # Record to search history
            context.history.add_entry(
                query=state["user_query"],
                results=search_results,
                is_valid=False,
                attempt=state["attempt"],
                plan=state["plan"],
            )

            logger.info(
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

            is_valid, summary, flagged = summarizer.summarize(
                state["user_query"], state["search_results"]
            )

            state["summary_valid"] = is_valid
            state["summary"] = summary

            # Add summary to message history
            summary_preview = summary[:150] + "..." if len(summary) > 150 else summary
            context.messages.append(AIMessage(f"Summary:\n{summary_preview}"))

            # Update validation status
            if is_valid:
                state["final_answer"] = summary
                state["execution_log"].append("✅ Summary validated successfully")
                context.metadata["validation_status"] = "VALID"
            else:
                state["execution_log"].append(
                    f"⚠️  Summary validation failed (Flagged: {', '.join(flagged)})"
                )
                context.metadata["validation_status"] = "INVALID"
                context.filters.add_flagged_sources(flagged)

            logger.info(
                f"Summarization complete: valid={is_valid}, flagged={len(flagged)}"
            )
            return state

        except Exception as e:
            logger.error(f"Error summarizing: {e}")
            state["execution_log"].append(f"❌ Error summarizing: {str(e)}")
            state["summary_valid"] = False
            state["summary"] = f"Error occurred during summarization: {str(e)}"
            return state

    # Conditional Logic

    def should_retry_plan(
        state: AgentState,
    ) -> Literal["optimize_plan", "execute_search"]:
        """Decide whether to retry plan optimization or proceed to execution."""
        if state["plan_valid"]:
            return "execute_search"
        else:
            return "optimize_plan"

    def should_retry_summary(state: AgentState) -> Literal["execute_search", "end"]:
        """Decide whether to retry search or end with current best answer."""
        if state["summary_valid"]:
            return "end"
        elif state["attempt"] < state["max_attempts"]:
            # Check if we have meaningful search results to retry with
            if not state["search_results"].strip():
                logger.warning(
                    f"No search results available on attempt {state['attempt']}, ending workflow"
                )
                state["final_answer"] = (
                    f"Unable to find sufficient information about: {state['user_query']}"
                )
                return "end"
            state["attempt"] += 1
            return "execute_search"
        else:
            # Provide fallback answer if we've exhausted attempts
            if not state["final_answer"].strip():
                state["final_answer"] = (
                    f"Search completed but unable to provide definitive answer for: {state['user_query']}"
                )
            return "end"

    workflow.add_node("generate_plan", node_generate_plan)
    workflow.add_node("optimize_plan", node_optimize_plan)
    workflow.add_node("execute_search", node_execute_search)
    workflow.add_node("summarize", node_summarize)

    workflow.add_edge(START, "generate_plan")
    workflow.add_edge("generate_plan", "optimize_plan")

    workflow.add_conditional_edges(
        "optimize_plan",
        should_retry_plan,
        {
            "optimize_plan": "optimize_plan",
            "execute_search": "execute_search",
        },
    )

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
