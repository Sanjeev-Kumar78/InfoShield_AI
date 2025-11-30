"""Data models for InfoShield AI."""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ActionType(str, Enum):
    """Action types for query responses."""
    IMMEDIATE_RESPONSE = "immediate_response"
    AUTOMATED_RESPONSE = "automated_response"
    HUMAN_VERIFICATION = "human_verification"
    GENERAL_INFO = "general_info"
    SYSTEM_ERROR = "system_error"


class Sentiment(str, Enum):
    """Sentiment classifications."""
    PANIC = "panic"
    URGENT = "urgent"
    CONCERNED = "concerned"
    NEUTRAL = "neutral"
    CURIOUS = "curious"


@dataclass
class QueryAnalysis:
    """Result of analyzing a user query."""
    sentiment: str
    urgency_score: int  # 1-10
    location: str
    disaster_type: Optional[str] = None
    is_emergency: bool = False
    keywords_found: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sentiment": self.sentiment,
            "urgency_score": self.urgency_score,
            "location": self.location,
            "disaster_type": self.disaster_type,
            "is_emergency": self.is_emergency,
            "keywords_found": self.keywords_found
        }


@dataclass
class CredibilityResult:
    """Result of credibility calculation."""
    score: int  # 0-100
    reasoning: str
    sources_found: List[str] = field(default_factory=list)
    official_sources_count: int = 0
    news_sources_count: int = 0

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "reasoning": self.reasoning,
            "sources_found": self.sources_found,
            "official_sources_count": self.official_sources_count,
            "news_sources_count": self.news_sources_count
        }


@dataclass
class HumanReviewEntry:
    """Entry for human verification queue."""
    session_id: str
    query: str
    location: str
    urgency_score: int
    credibility_score: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    reviewer_notes: str = ""

    def to_csv_row(self) -> List[str]:
        return [
            self.session_id,
            self.query,
            self.location,
            str(self.urgency_score),
            str(self.credibility_score),
            self.timestamp,
            self.status,
            self.reviewer_notes
        ]

    @staticmethod
    def csv_headers() -> List[str]:
        return [
            "session_id", "query", "location", "urgency_score",
            "credibility_score", "timestamp", "status", "reviewer_notes"
        ]
