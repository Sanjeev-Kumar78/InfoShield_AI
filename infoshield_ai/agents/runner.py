"""Multi-Agent Runner for InfoShield AI.

Provides execution capabilities for the multi-agent orchestration system
with proper error handling and human-in-the-loop integration.
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from infoshield_ai.config import (
    DEFAULT_USER_ID,
    CREDIBILITY_THRESHOLD,
    URGENCY_THRESHOLD
)
from infoshield_ai.agents.orchestrator import create_orchestrator_agent
from infoshield_ai.tools.human_review import save_for_human_review
from infoshield_ai.tools.guardrails import validate_query, get_rejection_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Error messages
ERROR_MESSAGES = {
    "api_error": "I apologize, but I'm experiencing technical difficulties connecting to my verification sources. Please try again in a moment. If this is an emergency, please contact local emergency services directly.",
    "timeout": "The verification is taking longer than expected. For urgent situations, please contact emergency services (911/112) while I continue processing.",
    "no_response": "I wasn't able to generate a complete response. Please try rephrasing your query or contact emergency services if this is urgent.",
    "rate_limit": "I'm currently handling many requests. Please wait a moment and try again. For emergencies, contact local emergency services.",
    "agent_error": "One of my specialized agents encountered an issue. I'll provide the best information available.",
}


def _extract_credibility_score(response: str) -> Optional[int]:
    """Extract credibility score from agent response."""
    patterns = [
        r'Credibility Score\s*[|\t]\s*(\d+)/100',  # Pipe or tab separator
        r'Credibility Score\s*\|\s*(\d+)/100',
        r'Score[:\s]+(\d+)/100',
        r'credibility[:\s]+(\d+)',
        r'(\d+)/100.*credibility',
    ]
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _extract_location(query: str) -> str:
    """Extract location from query."""
    words = query.split()
    for i, word in enumerate(words):
        if word.lower() in ['in', 'at', 'near'] and i + 1 < len(words):
            return ' '.join(words[i+1:i+3]).strip('?.,!')
    return "Unknown"


class MultiAgentRunner:
    """
    Runner for the multi-agent InfoShield AI system.

    Manages the orchestrator and its sub-agents, handling:
    - Session management
    - Error handling and recovery
    - Human-in-the-loop triggering
    - Response aggregation
    """

    def __init__(
        self,
        user_id: str = DEFAULT_USER_ID,
        enable_human_review: bool = True,
        verbose: bool = False
    ):
        """
        Initialize the multi-agent runner.

        Args:
            user_id: User identifier for session management.
            enable_human_review: Whether to trigger human review for low credibility.
            verbose: Whether to log detailed agent interactions.
        """
        self.user_id = user_id
        self.enable_human_review = enable_human_review
        self.verbose = verbose

        self.orchestrator = create_orchestrator_agent()
        self.session_service = InMemorySessionService()
        self.runner: Optional[Runner] = None
        self.session_id: Optional[str] = None
        self._initialized = False

        # Tracking
        self._query_count = 0
        self._error_count = 0
        self._agents_used: list = []

    async def _ensure_initialized(self) -> None:
        """Initialize session and runner if not already done."""
        if not self._initialized:
            import uuid
            self.session_id = f"multi_session_{uuid.uuid4().hex[:8]}"

            # Create session with initial state
            initial_state = {
                "query_count": 0,
                "current_date": datetime.now().strftime("%B %d, %Y"),
            }

            await self.session_service.create_session(
                app_name=self.orchestrator.name,
                user_id=self.user_id,
                session_id=self.session_id,
                state=initial_state  # Initialize state with memory context
            )

            self.runner = Runner(
                agent=self.orchestrator,
                app_name=self.orchestrator.name,
                session_service=self.session_service
            )

            self._initialized = True
            logger.info(
                f"Multi-agent system initialized. Session: {self.session_id}")

    async def process_query_async(self, query: str) -> Dict[str, Any]:
        """
        Process a disaster query through the multi-agent system.

        Args:
            query: User's disaster-related query.

        Returns:
            Dictionary containing:
            - response: The final response text
            - credibility_score: Extracted credibility score
            - agents_used: List of agents that participated
            - human_review: Human review info if triggered
            - metadata: Additional processing metadata
        """
        self._query_count += 1
        self._agents_used = []
        start_time = datetime.now()

        # === GUARDRAIL: Validate query before processing ===
        validation = validate_query(query)
        if not validation["is_valid"]:
            logger.info(
                f"Query rejected by guardrail: {validation['category']}")
            return {
                "response": get_rejection_response(validation),
                "credibility_score": None,
                "agents_used": ["guardrail"],
                "human_review": None,
                "metadata": {
                    "blocked": True,
                    "block_reason": validation["category"],
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }
            }

        try:
            await self._ensure_initialized()

            # Prepare message
            content = types.Content(
                role='user',
                parts=[types.Part(text=query)]
            )

            # Track events and agent transitions
            final_response = ""
            event_count = 0
            max_events = 100  # Higher limit for multi-agent

            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=content
            ):
                event_count += 1

                if event_count > max_events:
                    logger.warning("Event limit reached")
                    break

                # Track which agent is responding
                if hasattr(event, 'author') and event.author:
                    if event.author not in self._agents_used:
                        self._agents_used.append(event.author)
                        if self.verbose:
                            logger.info(f"Agent active: {event.author}")

                # Check for errors
                if hasattr(event, 'error_message') and event.error_message:
                    logger.error(f"Agent error: {event.error_message}")
                    self._error_count += 1

                # Capture final response
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text

            # Handle empty response
            if not final_response:
                self._error_count += 1
                return {
                    "response": ERROR_MESSAGES["no_response"],
                    "credibility_score": None,
                    "agents_used": self._agents_used,
                    "human_review": None,
                    "metadata": {"error": True, "event_count": event_count}
                }

            # Extract credibility and process human review
            credibility_score = _extract_credibility_score(final_response)
            human_review_info = None

            if self.enable_human_review and credibility_score is not None:
                if credibility_score < CREDIBILITY_THRESHOLD:
                    location = _extract_location(query)
                    urgency = 8 if any(kw in query.lower() for kw in [
                                       'emergency', 'help', 'urgent']) else 5

                    review_result = save_for_human_review(
                        query=query,
                        location=location,
                        urgency_score=urgency,
                        credibility_score=credibility_score
                    )

                    if review_result["status"] == "saved":
                        human_review_info = {
                            "session_id": review_result["session_id"],
                            "review_time": review_result["estimated_review_time"]
                        }

                        # Append notice to response (always add proper tracking info)
                        # Remove any incomplete human review text from synthesizer
                        final_response = re.sub(
                            r'This query has been flagged for human expert review\.?\s*Reference ID will be provided\.?',
                            '',
                            final_response
                        )
                        final_response += f"""

---
**🔍 Human Review Triggered**
- **Reference ID:** {review_result["session_id"]}
- **Estimated Review Time:** {review_result["estimated_review_time"]}
- **Reason:** Credibility score ({credibility_score}/100) below threshold ({CREDIBILITY_THRESHOLD})
"""

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Reset error count on success
            self._error_count = 0

            return {
                "response": final_response,
                "credibility_score": credibility_score,
                "agents_used": self._agents_used,
                "human_review": human_review_info,
                "metadata": {
                    "event_count": event_count,
                    "processing_time": processing_time,
                    "query_number": self._query_count
                }
            }

        except asyncio.TimeoutError:
            self._error_count += 1
            return {
                "response": ERROR_MESSAGES["timeout"],
                "credibility_score": None,
                "agents_used": self._agents_used,
                "human_review": None,
                "metadata": {"error": True, "error_type": "timeout"}
            }

        except Exception as e:
            self._error_count += 1
            logger.error(f"Multi-agent error: {type(e).__name__}: {str(e)}")

            error_str = str(e).lower()
            if 'rate' in error_str or 'quota' in error_str:
                error_msg = ERROR_MESSAGES["rate_limit"]
            elif 'timeout' in error_str:
                error_msg = ERROR_MESSAGES["timeout"]
            else:
                error_msg = ERROR_MESSAGES["api_error"]

            return {
                "response": error_msg,
                "credibility_score": None,
                "agents_used": self._agents_used,
                "human_review": None,
                "metadata": {"error": True, "error_type": type(e).__name__}
            }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Synchronous wrapper for process_query_async."""
        return asyncio.run(self.process_query_async(query))

    def get_status(self) -> Dict[str, Any]:
        """Get current runner status."""
        return {
            "initialized": self._initialized,
            "session_id": self.session_id,
            "query_count": self._query_count,
            "error_count": self._error_count,
            "healthy": self._error_count < 3,
            "agents": [
                "infoshield_orchestrator",
                "analyzer_agent",
                "search_agent",
                "credibility_agent"
            ]
        }


async def run_multi_agent_query(
    query: str,
    user_id: str = DEFAULT_USER_ID,
    enable_human_review: bool = True
) -> str:
    """
    Convenience function to run a single query through multi-agent system.

    Args:
        query: User's disaster query.
        user_id: User identifier.
        enable_human_review: Whether to enable human review.

    Returns:
        The final response string.
    """
    runner = MultiAgentRunner(
        user_id=user_id,
        enable_human_review=enable_human_review
    )
    result = await runner.process_query_async(query)
    return result["response"]
