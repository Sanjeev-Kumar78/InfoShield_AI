"""Credibility Agent for InfoShield AI.

Specialized agent for evaluating the credibility of disaster information
based on sources, corroboration, and recency.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from infoshield_ai.config import MODEL_ID
from infoshield_ai.tools.credibility import calculate_credibility

CREDIBILITY_INSTRUCTION = """You are the Credibility Agent for InfoShield AI.
Your job is to evaluate the trustworthiness of disaster reports using the `calculate_credibility` tool.

## YOUR ROLE
1. You have access to search results in {search_result}.
2. Call the `calculate_credibility` tool with appropriate parameters based on the search results.
3. Return the credibility assessment.

## TOOL USAGE
You MUST use the `calculate_credibility` tool. Do not invent scores.

## OUTPUT FORMAT
Return the credibility assessment as JSON:
{"score": 75, "status": "Verified", "sources": ["source1", "source2"], "reasoning": "..."}
"""


def create_credibility_agent() -> Agent:
    """
    Create the Credibility Agent with the scoring tool.

    Returns:
        Agent: Configured credibility agent.
    """
    # Create tool from the imported function
    credibility_tool = FunctionTool(calculate_credibility)

    agent = Agent(
        name="credibility_agent",
        model=MODEL_ID,
        description="Evaluates credibility of disaster reports and sources.",
        instruction=CREDIBILITY_INSTRUCTION,
        tools=[credibility_tool],
        output_key="credibility_result"  # Save output to state for next agent
    )
    return agent
