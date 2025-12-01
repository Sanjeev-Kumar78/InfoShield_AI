"""Guardrails for InfoShield AI.

Input validation to ensure queries are disaster-related and appropriate.
"""

import re
from typing import Dict, Any

# Keywords that indicate disaster-related queries
DISASTER_KEYWORDS = [
    # Natural disasters
    "flood", "flooding", "earthquake", "quake", "tsunami", "cyclone", "hurricane",
    "typhoon", "tornado", "storm", "wildfire", "fire", "landslide", "mudslide",
    "avalanche", "drought", "heatwave", "blizzard", "volcanic", "eruption",
    # Emergency situations
    "emergency", "disaster", "crisis", "evacuation", "rescue", "relief",
    "casualty", "casualties", "damage", "destroyed", "collapse", "trapped",
    # Weather events
    "heavy rain", "severe weather", "warning", "alert", "red alert", "orange alert",
    # Safety concerns
    "safe", "safety", "danger", "dangerous", "risk", "hazard", "threat",
    # Verification queries
    "is there", "is it true", "happening", "real", "fake", "rumor", "hoax",
    "verify", "confirm", "true or false", "fact check",
    # Location + event patterns
    "in india", "in japan", "in usa", "in california", "in tokyo", "in chennai",
    "in mumbai", "in delhi", "near", "around",
]

# Topics that are explicitly NOT allowed
OFF_TOPIC_PATTERNS = [
    r'^\d+\s*[\+\-\*\/]\s*\d+',  # Math operations like "3+4"
    r'^(what is|define|explain|how to|tutorial)',  # General knowledge
    r'(documentation|docs|api reference|library)',  # Documentation requests
    r'(code|programming|python|javascript|java\b)',  # Coding questions
    r'(recipe|cook|food|restaurant)',  # Food related
    r'(movie|music|song|game|sport)',  # Entertainment
    r'(stock|crypto|bitcoin|investment)',  # Finance
    r'(joke|funny|meme)',  # Entertainment
    r'^(hi|hello|hey|good morning|good evening)',  # Greetings
    r'(who are you|what are you|your name)',  # Bot identity questions
    # General weather (not disaster)
    r'(weather forecast|temperature tomorrow)',
]

# Technical/deployment patterns that must be rejected even if disaster words appear
TECH_OR_DEV_PATTERNS = [
    r'how\s+to\s+(deploy|install|build|set\s*up)',
    r'deploy(ing)?\s+(adk|agent|model|app|application|service)',
    r'\b(adk|sdk|docker|dockerfile|railway|vercel|cloud\s*run|github|gitlab)\b',
    r'code\s+(sample|snippet|example)',
    r'(write|generate)\s+code',
    r'(api\s+key|api\s+keys)',
    r'(documentation|docs|tutorial|guide)\s+(for|about)',
    r'install\s+(the\s+)?dependencies',
]


def validate_query(query: str) -> Dict[str, Any]:
    """
    Validate if a query is disaster-related and appropriate for InfoShield AI.

    Args:
        query: The user's input query.

    Returns:
        Dict containing:
        - is_valid: Boolean indicating if query is appropriate
        - reason: Explanation if query is rejected
        - category: "disaster", "off_topic", or "unclear"
    """
    query_lower = query.lower().strip()

    # Check if query is too short
    if len(query_lower) < 5:
        return {
            "is_valid": False,
            "reason": "Query is too short. Please provide more details about the disaster situation you want to verify.",
            "category": "unclear"
        }

    # Check for off-topic patterns first
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return {
                "is_valid": False,
                "reason": "I'm InfoShield AI, specialized in disaster information verification. I can help you verify disaster reports, check emergency situations, and provide safety information. Please ask about a specific disaster or emergency situation.",
                "category": "off_topic"
            }

    # Block technical/deployment/dev-ops requests regardless of disaster context
    for pattern in TECH_OR_DEV_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return {
                "is_valid": False,
                "reason": "I can't switch to development or deployment support. Please keep the conversation focused on verifying an actual disaster situation.",
                "category": "off_topic"
            }

    # Check if query contains disaster-related keywords
    has_disaster_keyword = any(
        keyword in query_lower for keyword in DISASTER_KEYWORDS)

    if has_disaster_keyword:
        return {
            "is_valid": True,
            "reason": "Query is disaster-related",
            "category": "disaster"
        }

    # If no disaster keywords found, check if it might be a location-based query
    # that could be about a disaster
    location_indicators = ["in", "at", "near", "around", "happening"]
    has_location_indicator = any(
        ind in query_lower for ind in location_indicators)

    # Check for question patterns about situations
    situation_patterns = [
        r'\?$',  # Ends with question mark
        r'^is\s',  # Starts with "is"
        r'^are\s',  # Starts with "are"
        r'^what.*happening',  # What's happening
        r'situation',
        r'status',
        r'update',
        r'news',
        r'report',
    ]

    is_situation_query = any(re.search(p, query_lower)
                             for p in situation_patterns)

    if has_location_indicator and is_situation_query:
        # Could be asking about a disaster situation - let it through with caution
        return {
            "is_valid": True,
            "reason": "Query appears to be about a situation at a location",
            "category": "disaster"
        }

    # Default: reject unclear queries
    return {
        "is_valid": False,
        "reason": "I'm InfoShield AI, designed specifically for disaster information verification. I can help you:\n\n• Verify disaster reports (floods, earthquakes, fires, storms)\n• Check emergency situations in specific locations\n• Assess the credibility of disaster-related news\n• Provide safety information during emergencies\n\nPlease ask about a specific disaster or emergency situation you'd like me to verify.",
        "category": "unclear"
    }


def get_rejection_response(validation_result: Dict[str, Any]) -> str:
    """
    Generate a polite rejection response for off-topic queries.

    Args:
        validation_result: Output from validate_query()

    Returns:
        Formatted rejection message
    """
    return f"""**🛡️ InfoShield AI - Query Outside Scope**

{validation_result['reason']}

**Example queries I can help with:**
- "Is there flooding in Chennai right now?"
- "Earthquake near Tokyo - is this real?"
- "What's the status of the California wildfires?"
- "Is the tsunami warning in Japan genuine?"

---
*InfoShield AI focuses exclusively on disaster verification to ensure accurate, life-saving information.*
"""
