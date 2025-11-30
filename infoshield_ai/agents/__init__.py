"""Multi-Agent Orchestration for InfoShield AI.

This module implements a multi-agent architecture where specialized agents
handle different aspects of disaster information verification:

1. Orchestrator Agent (Root) - Routes queries and coordinates responses
2. Search Agent - Performs real-time web searches using google_search
3. Analyzer Agent - Analyzes queries for sentiment, urgency, location
4. Credibility Agent - Evaluates source credibility and scores information
5. Response Agent - Formats final responses for users

Architecture:
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │   (Root Agent)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Search Agent  │   │Analyzer Agent │   │Credibility    │
│ (google_search)│   │ (analysis)    │   │   Agent       │
└───────────────┘   └───────────────┘   └───────────────┘
                             │
                             ▼
                    ┌───────────────┐
                    │Response Agent │
                    │ (formatting)  │
                    └───────────────┘
"""

from infoshield_ai.agents.orchestrator import (
    create_orchestrator_agent,
    root_agent
)
from infoshield_ai.agents.search_agent import create_search_agent
from infoshield_ai.agents.analyzer_agent import create_analyzer_agent
from infoshield_ai.agents.credibility_agent import create_credibility_agent
from infoshield_ai.agents.runner import MultiAgentRunner

__all__ = [
    "create_orchestrator_agent",
    "create_search_agent",
    "create_analyzer_agent",
    "create_credibility_agent",
    "MultiAgentRunner",
    "root_agent"
]
