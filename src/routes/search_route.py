from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Annotated, AsyncGenerator, Literal, Any
from src.agents.workflow.runner import run_search_agent_stream
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamEventData(BaseModel):
    attempt: int
    execution_log: list[str]
    plan: list[str] = Field(default_factory=list)
    search_results_length: int = 0
    summary_status: str = ""
    final_answer: str = ""


class StreamEvent(BaseModel):
    event_type: Literal["started", "node_completed", "completed", "error"] = Field(
        description="Type of event"
    )
    node_name: str | None = Field(default=None, description="Name of completed node")
    data: dict[str, Any]


class SearchResult(BaseModel):
    query: str
    final_answer: str
    execution_log: list[str]
    attempts: int
    flagged_sources: list[str] = Field(default_factory=list)


@router.get("/search", tags=["Search"])
async def search_stream(
    query: Annotated[str, Query(min_length=1, max_length=500)],
    max_attempts: Annotated[int, Query(ge=1, le=5)] = 3,
):
    """
    Perform a search query with SSE streaming updates.
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        # Send initial event
        start_event = StreamEvent(event_type="started", data={"query": query})
        yield f"data: {json.dumps(start_event.model_dump())}\n\n"

        final_state = None

        async for event in run_search_agent_stream(
            user_query=query, max_attempts=max_attempts
        ):
            for node_name, node_output in event.items():
                if node_name != "__end__":
                    event_data = StreamEventData(
                        attempt=node_output.get("attempt", 1),
                        execution_log=node_output.get("execution_log", []),
                        plan=node_output.get("plan", []),
                        search_results_length=len(
                            node_output.get("search_results", "")
                        ),
                        summary_status=str(node_output.get("summary_valid", "")),
                        final_answer=node_output.get("final_answer", ""),
                    )

                    stream_event = StreamEvent(
                        event_type="node_completed",
                        node_name=node_name,
                        data=event_data.model_dump(),
                    )

                    yield f"data: {json.dumps(stream_event.model_dump())}\n\n"

                final_state = node_output

        # Send search result
        if final_state:
            search_result = SearchResult(
                query=query,
                final_answer=final_state.get("final_answer", ""),
                execution_log=final_state.get("execution_log", []),
                attempts=final_state.get("attempts", final_state.get("attempt", 1)),
                flagged_sources=final_state.get("flagged_sources", []),
            )

            final_event = StreamEvent(
                event_type="completed", data=search_result.model_dump()
            )
            yield f"data: {json.dumps(final_event.model_dump())}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # For Nginx: disable response buffering
        },
    )
