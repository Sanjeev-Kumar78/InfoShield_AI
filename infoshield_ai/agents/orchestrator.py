"""Orchestrator Agent for InfoShield AI.

The root agent that coordinates the multi-agent workflow:
1. Receives user queries
2. Delegates to specialized sub-agents in sequence
3. Aggregates results into final response
"""

from datetime import datetime
from google.adk.agents import Agent, SequentialAgent
from infoshield_ai.config import MODEL_ID, URGENCY_THRESHOLD, CREDIBILITY_THRESHOLD
from infoshield_ai.agents.search_agent import create_search_agent
from infoshield_ai.agents.analyzer_agent import create_analyzer_agent
from infoshield_ai.agents.credibility_agent import create_credibility_agent

CURRENT_DATE = datetime.now().strftime("%B %d, %Y")

# Synthesizer agent instruction - creates the final report
SYNTHESIZER_INSTRUCTION = f"""You are the InfoShield AI Report Synthesizer.

**Today's Date: {CURRENT_DATE}**

## YOUR ROLE
You receive analysis results from the previous agents stored in session state and create a comprehensive verification report.

## AVAILABLE DATA (from state)
- {{analysis_result}}: JSON with sentiment, urgency, location, disaster_type, emergency
- {{search_result}}: Search results with sources and findings  
- {{credibility_result}}: Credibility score and verification status

## YOUR TASK
Create a comprehensive verification report using the EXACT format below.

## FINAL RESPONSE FORMAT

**📊 INFOSHIELD VERIFICATION REPORT**

| Metric | Value |
|--------|-------|
| Status | [Use status from credibility_result] |
| Credibility Score | [Score from credibility_result]/100 |
| Urgency Level | [From analysis_result: Low if urgency 1-3, Medium if 4-6, High if 7-8, Critical if 9-10] |
| Location | [From analysis_result] |
| Disaster Type | [From analysis_result] |
| Query Date | {CURRENT_DATE} |

**📋 Summary:**
[Summarize the search_result findings in bullet points]

**🛡️ Safety Advice:**
[Provide appropriate safety advice based on disaster type and urgency level as bullet points]

**📰 Sources:**
[List the key sources mentioned in search_result as bullet points]

**⚠️ Disclaimer:**
For life-threatening emergencies, contact local emergency services (911, 112) directly.
[If credibility score < {CREDIBILITY_THRESHOLD}: Add "⚠️ This query has been flagged for human expert review due to low credibility score."]
"""


def create_orchestrator_agent() -> Agent:
    """
    Create the Orchestrator (Root) Agent that coordinates sub-agents.

    Uses SequentialAgent to ensure all agents run in order:
    1. Analyzer Agent - analyzes query
    2. Search Agent - searches for information
    3. Credibility Agent - evaluates credibility
    4. Synthesizer Agent - creates final report

    Returns:
        Agent: Configured sequential orchestrator.
    """
    # Create sub-agents with output_key to store results in state
    analyzer = create_analyzer_agent()
    searcher = create_search_agent()
    credibility = create_credibility_agent()

    # Create synthesizer agent that reads from state and creates final report
    synthesizer = Agent(
        name="synthesizer_agent",
        model=MODEL_ID,
        description="Creates the final verification report from all agent outputs",
        instruction=SYNTHESIZER_INSTRUCTION,
    )

    # Create sequential orchestrator that runs agents in order
    orchestrator = SequentialAgent(
        name="infoshield_orchestrator",
        description="Sequential orchestrator for InfoShield AI multi-agent disaster verification system",
        sub_agents=[analyzer, searcher, credibility, synthesizer]
    )

    return orchestrator


# Expose root_agent at module level for ADK CLI compatibility
root_agent = create_orchestrator_agent()
