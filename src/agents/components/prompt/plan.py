PLAN_PROMPT = """You are an expert search strategist. Generate a concise, numbered search plan for {user_query} question.

CONSTRAINTS:
- Generate EXACTLY 3-4 focused search steps (not more)
- Each step must be a specific, actionable search query
- Avoid redundant or overlapping searches
- Prioritize breadth: cover different aspects of the query

Example for "What is the latest AI advancement in 2024?":
{{
    "steps": [
        "Latest AI breakthroughs 2024",
        "GPT-5 or Claude 4 release news 2024",
        "Multimodal AI improvements 2024"
    ]
}}"""
