"""Analyzer Agent for InfoShield AI.

Specialized agent for analyzing queries - sentiment, urgency,
location extraction, and disaster type identification.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from infoshield_ai.config import MODEL_ID_FAST
from infoshield_ai.tools.analyzer import analyze_query

ANALYZER_INSTRUCTION = """You are the Analyzer Agent for InfoShield AI.
Your job is to analyze disaster-related queries using the `analyze_query` tool.

## YOUR ROLE
1. Receive a query.
2. Call the `analyze_query` tool with:
   - `query`: The original query string.
3. Return the analysis results.

## TOOL USAGE
You MUST use the `analyze_query` tool for every request.

## OUTPUT FORMAT
Return ONLY the tool output as a JSON string. Example:
{"sentiment": "concerned", "urgency": 4, "location": "Japan", "disaster_type": "earthquake", "emergency": false}
"""


def create_analyzer_agent() -> Agent:
    """
    Create the Analyzer Agent with the analysis tool.

    Returns:
        Agent: Configured analyzer agent.
    """
    # Create tool from the imported function
    analysis_tool = FunctionTool(analyze_query)

    agent = Agent(
        name="analyzer_agent",
        model=MODEL_ID_FAST,
        description="Analyzes disaster queries for urgency, sentiment, and location.",
        instruction=ANALYZER_INSTRUCTION,
        tools=[analysis_tool],
        output_key="analysis_result"  # Save output to state for next agent
    )
    return agent
