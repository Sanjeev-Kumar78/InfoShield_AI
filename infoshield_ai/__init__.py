"""InfoShield AI - Disaster Information Verification System.

A multi-agent system built with Google ADK for real-time disaster query
verification with Human-in-the-Loop support.
"""

from infoshield_ai.agent import create_infoshield_agent, run_query

__version__ = "0.1.0"
__all__ = ["create_infoshield_agent", "run_query"]
