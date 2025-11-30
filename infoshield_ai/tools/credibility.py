"""Credibility scoring tool for InfoShield AI.

Calculates credibility scores based on search results and source reliability.
"""

from typing import Dict, Any, List
from infoshield_ai.config import OFFICIAL_SOURCES


def calculate_credibility(
    search_summary: str,
    sources_mentioned: str = "",
    location: str = "",
    disaster_type: str = ""
) -> Dict[str, Any]:
    """
    Calculate credibility score based on search results and sources.

    This tool analyzes the search results summary and source information
    to determine how credible a disaster report is.

    Scoring factors:
    - Official sources (+20 points each, max 40)
    - News sources (+10 points each, max 30)
    - Recency indicators (+10)
    - Location specificity (+10)
    - Corroboration (multiple sources) (+10)

    Args:
        search_summary: Summary of search results about the disaster report.
        sources_mentioned: Comma-separated list of sources found.
        location: Location from the query.
        disaster_type: Type of disaster if identified.

    Returns:
        Dictionary containing:
        - score: int - Credibility score from 0-100
        - reasoning: str - Explanation of the score
        - sources_found: list - List of identified sources
        - official_sources_count: int - Number of official sources
        - news_sources_count: int - Number of news sources

    Example:
        >>> result = calculate_credibility(
        ...     "NDRF confirms flooding in Chennai. Reuters reports heavy rain.",
        ...     "ndrf.gov.in, reuters.com",
        ...     "Chennai",
        ...     "flood"
        ... )
        >>> result["score"]
        75
    """
    search_lower = search_summary.lower()
    sources_lower = sources_mentioned.lower()

    score = 0
    reasons = []
    sources_found = []
    official_count = 0
    news_count = 0

    # Check for official sources
    for source in OFFICIAL_SOURCES:
        if source in search_lower or source in sources_lower:
            sources_found.append(source)
            if source in ["ndrf", "ndma", "fema", "government", "ministry", "official"]:
                official_count += 1
            else:
                news_count += 1

    # Score official sources (max 40)
    if official_count > 0:
        official_points = min(40, official_count * 20)
        score += official_points
        reasons.append(
            f"Found {official_count} official source(s) (+{official_points})")

    # Score news sources (max 30)
    if news_count > 0:
        news_points = min(30, news_count * 10)
        score += news_points
        reasons.append(
            f"Found {news_count} news/reliable source(s) (+{news_points})")

    # Check for recency indicators
    recency_keywords = ["today", "now", "just",
                        "breaking", "latest", "current", "ongoing"]
    if any(kw in search_lower for kw in recency_keywords):
        score += 10
        reasons.append("Recent/current event indicators (+10)")

    # Location specificity
    if location and location.lower() != "unknown":
        if location.lower() in search_lower:
            score += 10
            reasons.append(f"Location '{location}' confirmed in sources (+10)")

    # Multiple source corroboration
    if len(sources_found) >= 3:
        score += 10
        reasons.append("Multiple sources corroborate (+10)")

    # Disaster type confirmation
    if disaster_type and disaster_type.lower() in search_lower:
        score += 5
        reasons.append(f"Disaster type '{disaster_type}' confirmed (+5)")

    # Negative indicators
    doubt_keywords = ["unconfirmed", "rumor",
                      "false", "fake", "hoax", "not true", "denied"]
    if any(kw in search_lower for kw in doubt_keywords):
        score -= 30
        reasons.append("Found doubt/denial indicators (-30)")

    # Ensure score is within bounds
    score = max(0, min(100, score))

    # Generate reasoning
    if not reasons:
        reasons.append("No confirming sources found in search results")

    reasoning = "; ".join(reasons)

    return {
        "score": score,
        "reasoning": reasoning,
        "sources_found": sources_found,
        "official_sources_count": official_count,
        "news_sources_count": news_count
    }
