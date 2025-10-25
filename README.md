## LLM Search Agent

### Tech stack
- Python
    - Project uses a Python ecosystem suited for large LLMs. JavaScript was considered, but Python was chosen because this project focuses on a search agent rather than web scraping.  
- LangChain
    - LLM invocation and orchestration.  
- LangGraph
    - Context management and control flow.  
- Langfuse
    - Flexible observability with customizable options and self-hosting support.
- DuckDuckGo search: Free & Fast Search engine integration.   


### Workflow

1. Plan
    - The LLM generates a step-by-step plan to obtain the specific information requested by the user.

2. Action
    - Execute the validated plan.  

3. Summarize
    - Ensure the response appropriately addresses the user's intent and requirements.  
    - If not valid, identify the cause, update the context, and re-plan/re-optimize.  
    - If valid, stream the final answer to the user.  