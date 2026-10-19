import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
MAX_LOG_SIZE_MB = 10  # Maximum log file size before rotation
POPULARITY_SCALE_FACTOR = 10.0  # Scale factor for popularity scores


class BehaviorService:
    """Service for logging and analyzing user behavior patterns."""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure log file exists
        if not self.log_path.exists():
            self.log_path.touch()

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Appends an interaction event to the shadow logs.
        
        Args:
            event_type: Type of event (e.g., 'click_feedback', 'prediction_log')
            payload: Event data to log
        """
        try:
            log_entry = {
                **payload,
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
            # Check if log rotation is needed
            self._check_log_rotation()
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to log event '{event_type}': {e}")
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid payload for event '{event_type}': {e}")

    def get_scheme_popularity(self) -> Dict[str, float]:
        """
        Loads the logs and calculates a real-world popularity score (CTR-based).
        
        Returns:
            Dictionary mapping scheme_id to normalized popularity score (0-10)
        """
        if not self.log_path.exists():
            return {}
        
        try:
            logs = self._load_logs()
            if not logs:
                return {}
            
            df = pd.DataFrame(logs)
            if df.empty or 'scheme_id' not in df.columns:
                return {}
            
            # Filter for click feedback events
            click_events = df[df['event_type'] == 'click_feedback']
            if click_events.empty:
                return {}
            
            # Count clicks per scheme
            counts = click_events.groupby('scheme_id').size().to_dict()
            if not counts:
                return {}
            
            # Normalize to 0-10 scale
            max_count = max(counts.values())
            return {
                scheme_id: round((count / max_count) * POPULARITY_SCALE_FACTOR, 2)
                for scheme_id, count in counts.items()
            }
            
        except pd.errors.PandasError as e:
            logger.error(f"Pandas error while calculating popularity: {e}")
            return {}
        except (IOError, OSError) as e:
            logger.error(f"Failed to read log file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_scheme_popularity: {e}")
            return {}

    def get_user_interaction_count(self, scheme_id: str) -> int:
        """
        Get the number of interactions for a specific scheme.
        
        Args:
            scheme_id: The scheme identifier
            
        Returns:
            Number of recorded interactions
        """
        try:
            logs = self._load_logs()
            if not logs:
                return 0
            
            return sum(
                1 for log in logs 
                if log.get('scheme_id') == scheme_id and log.get('event_type') == 'click_feedback'
            )
        except Exception as e:
            logger.error(f"Failed to get interaction count: {e}")
            return 0

    def _load_logs(self) -> list[Dict[str, Any]]:
        """Load and parse all log entries from the log file."""
        logs = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            # Skip malformed log entries
                            continue
        except (IOError, OSError):
            pass
        return logs

    def _check_log_rotation(self) -> None:
        """Rotate log file if it exceeds maximum size."""
        try:
            if self.log_path.exists():
                size_mb = self.log_path.stat().st_size / (1024 * 1024)
                if size_mb > MAX_LOG_SIZE_MB:
                    # Archive old log
                    archive_path = self.log_path.with_suffix(
                        f".{datetime.now().strftime('%Y%m%d')}.old"
                    )
                    self.log_path.rename(archive_path)
                    self.log_path.touch()
                    logger.info(f"Rotated log file to {archive_path}")
        except (IOError, OSError) as e:
            logger.warning(f"Failed to rotate log file: {e}")
