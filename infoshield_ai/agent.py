"""InfoShield AI Root Agent.

The main orchestrator agent that coordinates disaster query processing
using Google Search and custom tools.
"""

import re
from infoshield_ai.config import (
    MODEL_ID,
    APP_NAME,
    DEFAULT_USER_ID,
    URGENCY_THRESHOLD,
    CREDIBILITY_THRESHOLD
)
from datetime import datetime
from infoshield_ai.tools import (
    analyze_query,
    calculate_credibility,
    save_for_human_review
)
import asyncio
import warnings
import logging
import sys
import io
from typing import Optional
from contextlib import contextmanager

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

# Suppress ADK warnings
warnings.filterwarnings('ignore', message='.*App name mismatch.*')
logging.getLogger('google.adk').setLevel(logging.ERROR)


@contextmanager
def suppress_stdout():
    """Context manager to suppress stdout messages (like ADK diagnostics)."""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = old_stdout


# Agent Instruction - The orchestration logic
CURRENT_DATE = datetime.now().strftime("%B %d, %Y")

AGENT_INSTRUCTION = f"""You are InfoShield AI, a disaster information verification assistant.
Your job is to help users by verifying disaster-related queries and providing accurate, 
actionable information.

**IMPORTANT: Today's date is {CURRENT_DATE}. Always focus on CURRENT, REAL-TIME information.**
**DO NOT report old news or past events as current. Only report what is happening RIGHT NOW.**

## WORKFLOW - Follow these steps for EVERY query:

### Step 1: Analyze the Query
Determine:
- Sentiment (panic, urgent, concerned, neutral, curious)
- Urgency score (1-10): How urgent is the user's need for information?
- Location mentioned
- Type of disaster (if any)

### Step 2: Gather REAL-TIME Information
If a location is identified, search for CURRENT information:
1. Search for CURRENT weather conditions at that location RIGHT NOW
2. Search for TODAY's news about any disasters in that area
3. Search for CURRENT official disaster alerts and warnings
4. Search for official Twitter/X posts from disaster management agencies

Use Google Search with queries that emphasize current/today:
- "[location] weather right now today {CURRENT_DATE}"
- "[location] [disaster_type] news today {CURRENT_DATE}"
- "[location] disaster alert warning current"
- "[location] live updates today"

**Twitter/X Searches for Official Updates:**
- "site:twitter.com [location] [disaster_type] alert"
- "site:x.com @NDMA_India [disaster_type]" (for India)
- "site:x.com @FEMA [disaster_type]" (for USA)
- "site:x.com @metoffice [location] warning" (for UK)
- "site:twitter.com @NDRFHQ [location]" (India NDRF)
- "site:twitter.com @NWS [location] alert" (US National Weather Service)
- "site:twitter.com @BOM_au [location]" (Australia Bureau of Meteorology)

### Step 3: Calculate Credibility Score (MANDATORY)
You MUST calculate and display a credibility score (0-100) based on:

**Scoring Criteria:**
- Official government sources (NDMA, FEMA, Met Dept, etc.): +25 points each (max 50)
- Major news agencies (Reuters, AP, BBC, etc.): +15 points each (max 30)
- Official Twitter/X handles confirm: +10 points
- Information is from TODAY/last 24 hours: +10 points
- Multiple sources corroborate: +10 points
- Location specificity matches query: +5 points

**Deductions:**
- Only social media/unverified sources: -20 points
- Information older than 48 hours: -15 points
- Conflicting reports: -10 points
- No official sources found: -25 points

### Step 4: Make Decision and Respond

**Decision Rules:**
- **Credibility >= {CREDIBILITY_THRESHOLD}**: Status = VERIFIED ✓
- **Credibility 40-{CREDIBILITY_THRESHOLD-1}**: Status = UNDER REVIEW (Human verification queued)
- **Credibility < 40**: Status = UNVERIFIED ⚠ (Low confidence, human review required)
- **Urgency >= {URGENCY_THRESHOLD}**: Add URGENT safety advice regardless of credibility

## RESPONSE FORMAT (STRICT - ALWAYS FOLLOW)

```
**📊 INFOSHIELD VERIFICATION REPORT**

| Metric | Value |
|--------|-------|
| Status | [VERIFIED ✓ / UNDER REVIEW 🔄 / UNVERIFIED ⚠] |
| Credibility Score | [X]/100 |
| Urgency Level | [Low/Medium/High/Critical] |
| Query Date | {CURRENT_DATE} |

**📋 Summary:**
[Your verified summary here]

**🛡️ Safety Advice:**
[Safety recommendations if applicable]

**📰 Sources:**
- [Source 1 with date]
- [Source 2 with date]

**⚠️ Disclaimer:**
For life-threatening emergencies, contact local emergency services (911, 112) directly.
[If credibility < {CREDIBILITY_THRESHOLD}: "This query has been flagged for human expert review. Reference ID will be provided."]
```

## CRITICAL GUIDELINES

- **ALWAYS include credibility score** - This is mandatory for every response
- **ONLY report CURRENT information** - never report old events as current
- If you find news from weeks/months ago, clearly state "No current reports found"
- Always specify the date of news articles you reference
- NEVER make up disaster information
- Always cite sources when providing verified information
- For high urgency queries, prioritize user safety over verification
- Be empathetic but clear and concise
- If credibility < {CREDIBILITY_THRESHOLD}, mention human review is triggered

## ERROR HANDLING
If you encounter any issues:
- Search fails: Respond with "I'm currently unable to verify this information due to a search issue. Please try again in a moment or contact emergency services if urgent."
- No results found: Respond with "No current reports found for this query. This could mean no disaster is occurring, or information isn't available yet."
- Ambiguous location: Ask user to clarify the specific location.
"""

# Error messages for graceful failure
ERROR_MESSAGES = {
    "api_error": "I apologize, but I'm experiencing technical difficulties connecting to my verification sources. Please try again in a moment. If this is an emergency, please contact local emergency services directly.",
    "timeout": "The verification is taking longer than expected. For urgent situations, please contact emergency services (911/112) while I continue processing.",
    "no_response": "I wasn't able to generate a complete response. Please try rephrasing your query or contact emergency services if this is urgent.",
    "rate_limit": "I'm currently handling many requests. Please wait a moment and try again. For emergencies, contact local emergency services.",
}


def create_infoshield_agent() -> Agent:
    """
    Create and return the InfoShield root agent.

    Returns:
        Agent: Configured InfoShield AI agent with tools.
    """
    agent = Agent(
        name="infoshield_ai",
        model=MODEL_ID,
        description="Disaster information verification assistant with real-time search capabilities.",
        instruction=AGENT_INSTRUCTION,
        tools=[
            google_search,      # Built-in tool for web search
            # Note: Cannot mix google_search with custom FunctionTools
            # Custom analysis is done via prompt engineering
        ]
    )
    return agent


# Expose root_agent at module level for ADK CLI compatibility
# This allows running: adk web infoshield_ai
root_agent = create_infoshield_agent()


def _extract_credibility_score(response: str) -> Optional[int]:
    """Extract credibility score from agent response."""
    # Look for patterns like "Credibility Score | 45/100" or "Credibility Score: 45"
    patterns = [
        r'Credibility Score\s*\|\s*(\d+)/100',
        r'Credibility Score[:\s]+(\d+)',
        r'credibility[:\s]+(\d+)',
        r'(\d+)/100.*credibility',
    ]
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _extract_location(query: str) -> str:
    """Extract location from query (simple heuristic)."""
    # Common location prepositions
    words = query.lower().split()
    for i, word in enumerate(words):
        if word in ['in', 'at', 'near', 'around'] and i + 1 < len(words):
            # Return the next word(s) as location
            return ' '.join(words[i+1:i+3]).strip('?.,!')
    return "Unknown"


async def run_query_async(
    query: str,
    user_id: str = DEFAULT_USER_ID,
    session_id: Optional[str] = None,
    enable_human_review: bool = True
) -> str:
    """
    Process a disaster query asynchronously with error handling and human-in-the-loop.

    Args:
        query: The user's disaster-related query.
        user_id: User identifier for session management.
        session_id: Optional specific session ID.
        enable_human_review: Whether to trigger human review for low credibility.

    Returns:
        str: The agent's response.
    """
    import uuid
    from asyncio import TimeoutError as AsyncTimeoutError

    try:
        # Create agent and session service (suppress ADK diagnostic messages)
        with suppress_stdout():
            agent = create_infoshield_agent()
            session_service = InMemorySessionService()

            # Generate session ID if not provided
            if session_id is None:
                session_id = f"session_{uuid.uuid4().hex[:8]}"

            # Create session - use agent.name to avoid mismatch
            session = await session_service.create_session(
                app_name=agent.name,
                user_id=user_id,
                session_id=session_id
            )

            # Create runner - use agent.name for consistency
            runner = Runner(
                agent=agent,
                app_name=agent.name,
                session_service=session_service
            )

        # Prepare message
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        # Run agent with timeout handling
        final_response = ""
        event_count = 0
        max_events = 50  # Safety limit

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            event_count += 1
            if event_count > max_events:
                logging.warning(f"Event limit reached for query: {query[:50]}")
                break

            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text

            # Check for errors in event
            if hasattr(event, 'error_message') and event.error_message:
                logging.error(f"Agent error: {event.error_message}")
                return ERROR_MESSAGES.get("api_error", ERROR_MESSAGES["no_response"])

        # Handle empty response
        if not final_response or final_response.strip() == "":
            return ERROR_MESSAGES["no_response"]

        # Post-processing: Human-in-the-loop for low credibility
        if enable_human_review:
            credibility_score = _extract_credibility_score(final_response)

            if credibility_score is not None and credibility_score < CREDIBILITY_THRESHOLD:
                # Extract location for human review
                location = _extract_location(query)

                # Determine urgency (simple heuristic)
                urgent_keywords = ['emergency', 'urgent',
                                   'help', 'trapped', 'sos', 'immediately']
                urgency_score = 8 if any(kw in query.lower()
                                         for kw in urgent_keywords) else 5

                # Save for human review
                review_result = save_for_human_review(
                    query=query,
                    location=location,
                    urgency_score=urgency_score,
                    credibility_score=credibility_score
                )

                # Append human review notice to response
                if review_result["status"] == "saved":
                    human_review_notice = f"""

---
**🔍 Human Review Triggered**
Your query has been flagged for expert verification due to low credibility score ({credibility_score}/100).
- **Reference ID:** {review_result["session_id"]}
- **Estimated Review Time:** {review_result["estimated_review_time"]}

Our human experts will verify this information. You can check the status using your reference ID.
"""
                    final_response += human_review_notice

        return final_response

    except AsyncTimeoutError:
        logging.error(f"Timeout processing query: {query[:50]}")
        return ERROR_MESSAGES["timeout"]

    except Exception as e:
        error_type = type(e).__name__
        logging.error(f"Error processing query ({error_type}): {str(e)}")

        # Check for specific error types
        error_str = str(e).lower()
        if 'rate' in error_str or 'quota' in error_str:
            return ERROR_MESSAGES["rate_limit"]
        elif 'timeout' in error_str or 'timed out' in error_str:
            return ERROR_MESSAGES["timeout"]
        else:
            return ERROR_MESSAGES["api_error"]


def run_query(
    query: str,
    user_id: str = DEFAULT_USER_ID,
    session_id: Optional[str] = None,
    enable_human_review: bool = True
) -> str:
    """
    Process a disaster query synchronously.

    This is a convenience wrapper around the async function.

    Args:
        query: The user's disaster-related query.
        user_id: User identifier for session management.
        session_id: Optional specific session ID.
        enable_human_review: Whether to trigger human review for low credibility.

    Returns:
        str: The agent's response.
    """
    return asyncio.run(run_query_async(query, user_id, session_id, enable_human_review))


class InfoShieldRunner:
    """
    A stateful runner for InfoShield AI that maintains session context.

    Use this for continuous conversations where context should persist.
    Includes error handling and human-in-the-loop functionality.
    """

    def __init__(self, user_id: str = DEFAULT_USER_ID, enable_human_review: bool = True):
        """Initialize the runner with a user ID."""
        self.user_id = user_id
        self.enable_human_review = enable_human_review
        self.agent = create_infoshield_agent()
        self.session_service = InMemorySessionService()
        self.runner: Optional[Runner] = None
        self.session_id: Optional[str] = None
        self._initialized = False
        self._error_count = 0
        self._max_consecutive_errors = 3

    async def _ensure_initialized(self) -> None:
        """Ensure session and runner are initialized."""
        if not self._initialized:
            import uuid
            self.session_id = f"session_{uuid.uuid4().hex[:8]}"

            await self.session_service.create_session(
                app_name=self.agent.name,
                user_id=self.user_id,
                session_id=self.session_id
            )

            self.runner = Runner(
                agent=self.agent,
                app_name=self.agent.name,
                session_service=self.session_service
            )

            self._initialized = True

    async def process_query_async(self, query: str) -> str:
        """Process a query asynchronously with error handling."""
        from asyncio import TimeoutError as AsyncTimeoutError

        try:
            await self._ensure_initialized()

            content = types.Content(
                role='user',
                parts=[types.Part(text=query)]
            )

            final_response = ""
            event_count = 0
            max_events = 50

            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=content
            ):
                event_count += 1
                if event_count > max_events:
                    break

                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text

                # Check for errors
                if hasattr(event, 'error_message') and event.error_message:
                    self._error_count += 1
                    if self._error_count >= self._max_consecutive_errors:
                        return f"{ERROR_MESSAGES['api_error']}\n\n(Multiple consecutive errors detected. The service may be temporarily unavailable.)"
                    return ERROR_MESSAGES["api_error"]

            # Handle empty response
            if not final_response or final_response.strip() == "":
                self._error_count += 1
                return ERROR_MESSAGES["no_response"]

            # Reset error count on success
            self._error_count = 0

            # Post-processing: Human-in-the-loop
            if self.enable_human_review:
                credibility_score = _extract_credibility_score(final_response)

                if credibility_score is not None and credibility_score < CREDIBILITY_THRESHOLD:
                    location = _extract_location(query)
                    urgent_keywords = ['emergency',
                                       'urgent', 'help', 'trapped', 'sos']
                    urgency_score = 8 if any(kw in query.lower()
                                             for kw in urgent_keywords) else 5

                    review_result = save_for_human_review(
                        query=query,
                        location=location,
                        urgency_score=urgency_score,
                        credibility_score=credibility_score
                    )

                    if review_result["status"] == "saved":
                        final_response += f"""

---
**🔍 Human Review Triggered**
- **Reference ID:** {review_result["session_id"]}
- **Estimated Review Time:** {review_result["estimated_review_time"]}
- **Reason:** Credibility score ({credibility_score}/100) below threshold ({CREDIBILITY_THRESHOLD})
"""

            return final_response

        except AsyncTimeoutError:
            self._error_count += 1
            return ERROR_MESSAGES["timeout"]

        except Exception as e:
            self._error_count += 1
            error_str = str(e).lower()

            if 'rate' in error_str or 'quota' in error_str:
                return ERROR_MESSAGES["rate_limit"]
            elif 'timeout' in error_str:
                return ERROR_MESSAGES["timeout"]
            else:
                logging.error(
                    f"InfoShieldRunner error: {type(e).__name__}: {str(e)}")
                return ERROR_MESSAGES["api_error"]

    def process_query(self, query: str) -> str:
        """Process a query synchronously."""
        return asyncio.run(self.process_query_async(query))

    def get_error_status(self) -> dict:
        """Get current error status."""
        return {
            "consecutive_errors": self._error_count,
            "max_errors": self._max_consecutive_errors,
            "healthy": self._error_count < self._max_consecutive_errors
        }
