"""Search Agent for InfoShield AI.

Specialized agent for performing real-time web searches to gather
disaster information from multiple sources.
"""

from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools import google_search
from infoshield_ai.config import MODEL_ID

CURRENT_DATE = datetime.now().strftime("%B %d, %Y")

SEARCH_AGENT_INSTRUCTION = f"""You are the Search Agent for InfoShield AI.
Your ONLY job is to search for CURRENT, REAL-TIME disaster information.

**Today's date: {CURRENT_DATE}**

## YOUR ROLE
You receive queries and have access to analysis results in {{analysis_result}}.
Extract the location and disaster_type from the analysis, then perform searches.
DO NOT analyze or verify - just search and return what you find.

## SEARCH STRATEGY
For disaster queries, perform multiple targeted searches:

1. **Current News Search:**
   "[location] [disaster_type] news today {CURRENT_DATE}"

2. **Official Alerts Search:**
   "[location] disaster alert warning official"

3. **Weather/Conditions Search:**
   "[location] weather conditions current"

4. **Twitter/Social Updates:**
   "site:twitter.com OR site:x.com [location] [disaster_type] alert"

## OUTPUT FORMAT
Return your findings in this EXACT format:

```
SEARCH_RESULTS:
---
Query 1: [your search query]
Results: [summarize top 3-5 results with source names and dates]
---
Query 2: [your search query]
Results: [summarize top 3-5 results with source names and dates]
---
Sources Found:
- [Source 1] (date)
- [Source 2] (date)
---
Official Sources Mentioned: [list any government/official sources]
News Sources Mentioned: [list any major news outlets]
Social Media Mentions: [any verified social media updates]
```

## IMPORTANT
- Focus on CURRENT information only
- Note the date of each source
- Flag if information is old (>48 hours)
- Report if no current information found
"""


def create_search_agent() -> Agent:
    """
    Create the Search Agent specialized for web searches.

    This agent uses google_search tool exclusively to gather
    real-time disaster information.

    Returns:
        Agent: Configured search agent with google_search tool.
    """
    return Agent(
        name="search_agent",
        model=MODEL_ID,
        description="Specialized agent for real-time disaster information search",
        instruction=SEARCH_AGENT_INSTRUCTION,
        tools=[google_search],
        output_key="search_result"  # Save output to state for next agent
    )
