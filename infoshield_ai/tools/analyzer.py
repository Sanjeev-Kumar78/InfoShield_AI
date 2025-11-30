"""Query analysis tool for InfoShield AI.

Analyzes user queries for sentiment, urgency, and location extraction.
"""

import re
from typing import Dict, Any
from infoshield_ai.config import DISASTER_KEYWORDS


def analyze_query(query: str, inferred_location: str = None) -> Dict[str, Any]:
    """
    Analyze a disaster-related query for sentiment, urgency, and location.

    This tool performs rule-based analysis to extract:
    - Sentiment (panic, urgent, concerned, neutral, curious)
    - Urgency score (1-10)
    - Location mentioned in the query (or inferred by the agent)
    - Disaster type if identifiable
    - Emergency indicators

    Args:
        query: The user's disaster-related query string.
        inferred_location: Optional location inferred by the calling agent.

    Returns:
        Dictionary containing analysis results with keys:
        - sentiment: str - Emotional tone of the query
        - urgency_score: int - Urgency level from 1-10
        - location: str - Extracted location or "Unknown"
        - disaster_type: str - Type of disaster if identified
        - is_emergency: bool - Whether query indicates emergency
        - keywords_found: list - Disaster keywords detected

    Example:
        >>> result = analyze_query("Help! Flooding in Mumbai!", inferred_location="Mumbai")
        >>> result["urgency_score"]
        9
        >>> result["location"]
        "Mumbai"
    """
    query_lower = query.lower()

    # Detect disaster keywords
    keywords_found = [kw for kw in DISASTER_KEYWORDS if kw in query_lower]

    # Urgency indicators
    panic_indicators = ["help", "sos", "emergency",
                        "trapped", "dying", "drowning"]
    urgent_indicators = ["now", "immediately",
                         "urgent", "quickly", "asap", "!"]

    # Calculate urgency score
    urgency_score = 3  # Base score

    if any(ind in query_lower for ind in panic_indicators):
        urgency_score += 4
    if any(ind in query_lower for ind in urgent_indicators):
        urgency_score += 2
    if query.count("!") >= 2:
        urgency_score += 1
    if len(keywords_found) > 0:
        urgency_score += len(keywords_found)

    urgency_score = min(10, max(1, urgency_score))  # Clamp to 1-10

    # Determine sentiment
    if urgency_score >= 8:
        sentiment = "panic"
    elif urgency_score >= 6:
        sentiment = "urgent"
    elif urgency_score >= 4:
        sentiment = "concerned"
    elif "?" in query and len(keywords_found) == 0:
        sentiment = "curious"
    else:
        sentiment = "neutral"

    # Extract location
    location = "Unknown"

    # Use inferred location if provided and valid
    if inferred_location and inferred_location.lower() != "unknown":
        location = inferred_location
    else:
        # Fallback to regex pattern matching
        location_patterns = [
            r"in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"near\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:area|region|city|town|district)"
        ]

        for pattern in location_patterns:
            match = re.search(pattern, query)
            if match:
                location = match.group(1)
                break

    # Identify disaster type
    disaster_type = None
    disaster_mapping = {
        "flood": ["flood", "flooding", "water entering"],
        "earthquake": ["earthquake", "quake", "tremor", "seismic"],
        "tsunami": ["tsunami", "tidal wave"],
        "cyclone": ["cyclone", "hurricane", "typhoon", "storm"],
        "fire": ["fire", "wildfire", "blaze", "burning"],
        "landslide": ["landslide", "mudslide", "debris"],
    }

    for dtype, keywords in disaster_mapping.items():
        if any(kw in query_lower for kw in keywords):
            disaster_type = dtype
            break

    # Is this an emergency?
    is_emergency = urgency_score >= 8 or any(
        ind in query_lower for ind in panic_indicators)

    return {
        "sentiment": sentiment,
        "urgency_score": urgency_score,
        "location": location,
        "disaster_type": disaster_type,
        "is_emergency": is_emergency,
        "keywords_found": keywords_found
    }
