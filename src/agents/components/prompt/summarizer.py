from langchain_core.prompts import PromptTemplate


SUMMARIZE_SYSTEM_PROMPT = """You are an information synthesizer. Create a comprehensive answer from search results.

VALIDATION CRITERIA (answer is VALID if):
1. ✓ Directly answers the user's query
2. ✓ Backed by multiple credible sources
3. ✓ No obvious misinformation or contradictions
4. ✓ Sufficient detail and clarity

FLAGGING SOURCES:
- Mark as unreliable: outdated sites, spam, commercial only, obvious bias
- Domain examples to flag: "domain.fandom.com", "sketchy-blog.net"
- Keep only clearly problematic domains"""

SYNTHESIS_PROMPT = PromptTemplate.from_template(
    template="""User Query: {user_query}

Search Results:
{search_results}

Please synthesize these results into a comprehensive answer and validate its quality.""",
)
