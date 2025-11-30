"""Human-in-the-loop review management for InfoShield AI.

Handles saving and retrieving queries that need human expert verification.
"""

import os
import csv
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from infoshield_ai.config import PENDING_VERIFICATIONS_PATH
from infoshield_ai.models import HumanReviewEntry


def _ensure_csv_exists() -> None:
    """Ensure the CSV file and its directory exist."""
    os.makedirs(os.path.dirname(PENDING_VERIFICATIONS_PATH), exist_ok=True)

    if not os.path.exists(PENDING_VERIFICATIONS_PATH):
        with open(PENDING_VERIFICATIONS_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(HumanReviewEntry.csv_headers())


def save_for_human_review(
    query: str,
    location: str,
    urgency_score: int,
    credibility_score: int
) -> Dict[str, Any]:
    """
    Save a query for human expert verification.

    When a query has low credibility or needs manual verification,
    this tool saves it to a CSV queue for human experts to review.

    Args:
        query: The original user query.
        location: Extracted or provided location.
        urgency_score: Urgency score from analysis (1-10).
        credibility_score: Calculated credibility score (0-100).

    Returns:
        Dictionary containing:
        - session_id: str - Unique identifier for tracking
        - status: str - "saved" or "error"
        - message: str - Success/error message
        - estimated_review_time: str - Estimated time for review

    Example:
        >>> result = save_for_human_review(
        ...     "Aliens attacking city center!",
        ...     "Unknown",
        ...     5,
        ...     15
        ... )
        >>> result["session_id"]
        "IS-abc12345"
    """
    try:
        _ensure_csv_exists()

        # Generate unique session ID
        session_id = f"IS-{uuid.uuid4().hex[:8]}"

        # Create entry
        entry = HumanReviewEntry(
            session_id=session_id,
            query=query,
            location=location,
            urgency_score=urgency_score,
            credibility_score=credibility_score
        )

        # Append to CSV
        with open(PENDING_VERIFICATIONS_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(entry.to_csv_row())

        # Estimate review time based on urgency
        if urgency_score >= 8:
            review_time = "within 15 minutes"
        elif urgency_score >= 5:
            review_time = "within 1 hour"
        else:
            review_time = "within 24 hours"

        return {
            "session_id": session_id,
            "status": "saved",
            "message": f"Query saved for human verification. Your reference ID is {session_id}.",
            "estimated_review_time": review_time
        }

    except Exception as e:
        return {
            "session_id": "",
            "status": "error",
            "message": f"Failed to save for review: {str(e)}",
            "estimated_review_time": "unknown"
        }


def get_pending_reviews(status_filter: Optional[str] = "pending") -> Dict[str, Any]:
    """
    Retrieve pending human verification entries.

    Used by the human review dashboard to fetch queries awaiting review.

    Args:
        status_filter: Filter by status ("pending", "reviewed", "all").

    Returns:
        Dictionary containing:
        - count: int - Number of entries found
        - entries: list - List of pending review entries
        - status: str - "success" or "error"
    """
    try:
        _ensure_csv_exists()

        entries = []
        with open(PENDING_VERIFICATIONS_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if status_filter == "all" or row.get("status", "pending") == status_filter:
                    entries.append(row)

        return {
            "count": len(entries),
            "entries": entries,
            "status": "success"
        }

    except Exception as e:
        return {
            "count": 0,
            "entries": [],
            "status": "error",
            "message": str(e)
        }


def update_review_status(
    session_id: str,
    new_status: str,
    reviewer_notes: str = ""
) -> Dict[str, Any]:
    """
    Update the status of a human review entry.

    Used by human reviewers to mark entries as reviewed/verified.

    Args:
        session_id: The unique session ID to update.
        new_status: New status ("verified", "rejected", "needs_more_info").
        reviewer_notes: Optional notes from the reviewer.

    Returns:
        Dictionary with update status.
    """
    try:
        _ensure_csv_exists()

        # Read all entries
        entries = []
        found = False
        with open(PENDING_VERIFICATIONS_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                if row.get("session_id") == session_id:
                    row["status"] = new_status
                    row["reviewer_notes"] = reviewer_notes
                    found = True
                entries.append(row)

        if not found:
            return {
                "status": "error",
                "message": f"Session ID {session_id} not found"
            }

        # Write back
        with open(PENDING_VERIFICATIONS_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(entries)

        return {
            "status": "success",
            "message": f"Updated {session_id} to status: {new_status}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
