"""Investigation History Service - stores and retrieves investigation history."""

import uuid
from datetime import datetime
from typing import Any

from core.logging import logger

# In-memory store for investigation history (replace with InsForge database later)
_investigation_history: list[dict[str, Any]] = []


class InvestigationHistoryService:
    """Service for managing investigation history."""

    def save(self, investigation: dict[str, Any]) -> dict[str, Any]:
        """Save an investigation to history."""
        record = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.utcnow().isoformat(),
            "namespace": investigation.get("namespace", "default"),
            "context": investigation.get("context"),
            "root_cause": investigation.get("diagnosis", {}).get("root_cause", "Unknown"),
            "confidence": investigation.get("diagnosis", {}).get("confidence", 0),
            "status": self._determine_status(investigation),
            "details": investigation,
        }
        _investigation_history.insert(0, record)
        # Keep only last 100 investigations
        if len(_investigation_history) > 100:
            _investigation_history.pop()
        logger.info(f"Saved investigation to history: {record['id']}")
        return record

    def get_all(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get investigation history."""
        return _investigation_history[:limit]

    def get_by_id(self, investigation_id: str) -> dict[str, Any] | None:
        """Get a specific investigation by ID."""
        for record in _investigation_history:
            if record["id"] == investigation_id:
                return record
        return None

    def _determine_status(self, investigation: dict[str, Any]) -> str:
        """Determine investigation status."""
        diagnosis = investigation.get("diagnosis", {})
        root_cause = diagnosis.get("root_cause", "").lower()

        if "failed" in root_cause or "error" in root_cause or "unavailable" in root_cause:
            return "failed"
        if "no issues" in root_cause or "healthy" in root_cause:
            return "no_issues"
        return "completed"


_history_service: InvestigationHistoryService | None = None


def get_history_service() -> InvestigationHistoryService:
    """Get or create history service singleton."""
    global _history_service
    if _history_service is None:
        _history_service = InvestigationHistoryService()
    return _history_service
