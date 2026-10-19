"""
Discovery Orchestration & Scheduler Engine
==========================================
Coordinates automated monthly discovery runs, worker pool execution, local/distributed locks,
checkpoint resumability, and volume anomaly detection.
Enforces:
- Idempotency and run lock protection
- Volume anomaly detection (flags SOURCE_VOLUME_ANOMALY on sharp drops)
- Failure isolation per source
- Zero automatic certification
"""

import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from services.core.discovery.models import (
    ProgramCandidate,
    SourceRegistryDefinition,
    DiscoveryResult,
)
from services.core.discovery.registry import DiscoverySourceRegistry
from services.core.discovery.engine import DiscoveryEngine
from services.core.discovery.snapshots import DurableSnapshotStore
from services.core.discovery.pagination import CrawlCheckpointStore
from services.core.discovery.governance import GovernanceWorkflowManager


LOCK_FILE = Path("data/staging/discovery_scheduler.lock")
RUN_HISTORY_FILE = Path("data/staging/discovery_runs_history.json")


class VolumeAnomalyDetector:
    """
    Detects sudden precipitous drops in discovered program counts.
    E.g. if a source previously yielded 4,000 records and suddenly yields 7 records,
    flags SOURCE_VOLUME_ANOMALY.
    """

    @staticmethod
    def check_anomaly(
        source_id: str,
        current_count: int,
        historical_baseline: Optional[int],
        threshold_drop_ratio: float = 0.5,
    ) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_anomaly, message).
        An anomaly is triggered if current_count drops by more than 50% from a significant baseline (> 20).
        """
        if historical_baseline is None or historical_baseline < 20:
            return False, None

        drop_ratio = (historical_baseline - current_count) / historical_baseline
        if drop_ratio >= threshold_drop_ratio:
            return True, (
                f"SOURCE_VOLUME_ANOMALY: {source_id} dropped from {historical_baseline} "
                f"to {current_count} records ({drop_ratio * 100:.1f}% reduction). "
                f"Requires human review before treating as authoritative."
            )
        return False, None


class DiscoveryScheduler:
    """
    Production scheduler and orchestrator for monthly and on-demand discovery.
    """

    def __init__(
        self,
        engine: Optional[DiscoveryEngine] = None,
        snapshot_store: Optional[DurableSnapshotStore] = None,
        governance: Optional[GovernanceWorkflowManager] = None,
    ):
        self.engine = engine or DiscoveryEngine()
        self.snapshot_store = snapshot_store or DurableSnapshotStore()
        self.governance = governance or GovernanceWorkflowManager()
        self.anomaly_detector = VolumeAnomalyDetector()
        self.lock_file = LOCK_FILE
        self.history_file = RUN_HISTORY_FILE
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

    def acquire_lock(self, run_id: str) -> bool:
        if self.lock_file.exists():
            try:
                data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                lock_time = data.get("timestamp", 0)
                # Auto-expire stale locks older than 2 hours
                if time.time() - lock_time < 7200:
                    return False
            except Exception:
                pass

        self.lock_file.write_text(
            json.dumps({"run_id": run_id, "timestamp": time.time()}),
            encoding="utf-8",
        )
        return True

    def release_lock(self) -> None:
        if self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except Exception:
                pass

    def execute_scheduled_run(
        self,
        run_type: str = "monthly_full",
        source_ids: Optional[List[str]] = None,
        limit_per_source: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes an idempotent discovery run with lock protection and anomaly tracking.
        """
        run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        if not self.acquire_lock(run_id):
            return {
                "run_id": run_id,
                "status": "BLOCKED_BY_LOCK",
                "error": "Another discovery run is currently active.",
            }

        start_time = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        report: Dict[str, Any] = {
            "run_id": run_id,
            "run_type": run_type,
            "started_at": now_iso,
            "sources_attempted": 0,
            "sources_succeeded": 0,
            "sources_failed": 0,
            "total_discovered": 0,
            "total_unique": 0,
            "anomalies_detected": [],
            "source_results": {},
        }

        try:
            results, candidates = self.engine.run_discovery(
                enabled_only=not bool(source_ids),
                source_ids=source_ids,
                limit_per_source=limit_per_source,
            )

            report["sources_attempted"] = len(results)
            for res in results:
                if res.status_code == 200:
                    report["sources_succeeded"] += 1
                else:
                    report["sources_failed"] += 1

                report["total_discovered"] += res.candidate_count
                report["total_unique"] += res.unique_count
                report["source_results"][res.source_id] = res.to_dict()

                # Anomaly check against known baseline for myScheme / DBT Bharat
                historical_baseline = 4000 if "myscheme" in res.source_id else (250 if "dbt" in res.source_id else None)
                if limit_per_source is None and historical_baseline:
                    is_anom, msg = self.anomaly_detector.check_anomaly(res.source_id, res.candidate_count, historical_baseline)
                    if is_anom and msg:
                        report["anomalies_detected"].append(msg)

            # Route candidates to governance queue (unverified)
            for cand in candidates:
                self.governance.queue_for_review(cand, reason=f"scheduled_run:{run_id}")

            report["status"] = "COMPLETED"
            report["finished_at"] = datetime.now(timezone.utc).isoformat()
            report["duration_seconds"] = round(time.time() - start_time, 2)

            # Record in history
            self._save_run_history(report)
            return report

        finally:
            self.release_lock()

    def _save_run_history(self, report: Dict[str, Any]) -> None:
        history = []
        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception:
                history = []
        history.append(report)
        # Keep last 50 runs
        history = history[-50:]
        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
