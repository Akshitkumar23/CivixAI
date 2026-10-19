"""
Source Freshness Policies & Status Evaluator
Calculates source staleness, recheck requirements, and freshness states based on trust tier policies.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from services.core.database.models import SourceRegistry

FRESHNESS_STATUSES = ["fresh", "needs_recheck", "source_changed", "stale", "unreachable"]

class FreshnessEvaluator:
    @staticmethod
    def evaluate_source(source: SourceRegistry, now_utc: Optional[datetime] = None) -> str:
        """
        Evaluates current freshness status for a SourceRegistry record.
        """
        now = now_utc or datetime.now(timezone.utc)

        if source.freshness_status == "unreachable":
            return "unreachable"

        if not source.last_checked_at:
            return "needs_recheck"

        # Make sure tz-aware
        last_checked = source.last_checked_at
        if last_checked.tzinfo is None:
            last_checked = last_checked.replace(tzinfo=timezone.utc)

        days_since_check = (now - last_checked).total_seconds() / 86400.0
        policy_days = source.freshness_policy_days or 30

        if days_since_check > (policy_days * 1.5):
            return "stale"
        elif days_since_check > policy_days:
            return "needs_recheck"
        elif source.freshness_status == "source_changed":
            return "source_changed"
        else:
            return "fresh"

    @classmethod
    def audit_all_sources(cls, db: Session) -> Dict[str, Any]:
        """Audits all registered sources in the database and updates their status."""
        sources = db.query(SourceRegistry).all()
        now = datetime.now(timezone.utc)
        stats = {"fresh": 0, "needs_recheck": 0, "source_changed": 0, "stale": 0, "unreachable": 0}

        for src in sources:
            new_status = cls.evaluate_source(src, now_utc=now)
            if src.freshness_status != new_status and src.freshness_status != "source_changed":
                src.freshness_status = new_status
            stats[src.freshness_status] = stats.get(src.freshness_status, 0) + 1

        db.commit()
        return stats
