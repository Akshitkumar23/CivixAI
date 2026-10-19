"""
Pagination, Checkpoint & Resumability Controller
================================================
Provides reusable pagination strategies (page traversal, cursor, token, offset)
and durable crawl checkpointing.
Enforces:
- Exhaustive pagination until true source termination
- Loop / duplicate page detection
- Progress persistence and resumption without restarting from zero
- Zero silent truncation
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple, Set
from datetime import datetime, timezone
import hashlib


CHECKPOINT_FILE = Path("data/staging/crawl_checkpoints.json")


class CrawlCheckpointStore:
    """
    Manages persistent state for multi-source crawler checkpoints.
    Enables resuming interrupted crawl runs.
    """

    def __init__(self, checkpoint_path: Optional[Path] = None):
        self.path = checkpoint_path or CHECKPOINT_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._checkpoints: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        temp_file = self.path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self._checkpoints, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.path)

    def get_checkpoint(self, source_id: str) -> Optional[Dict[str, Any]]:
        return self._checkpoints.get(source_id)

    def update_checkpoint(
        self,
        source_id: str,
        last_page: int,
        last_cursor: Optional[str] = None,
        total_discovered: int = 0,
        completed: bool = False,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        self._checkpoints[source_id] = {
            "source_id": source_id,
            "last_page": last_page,
            "last_cursor": last_cursor,
            "total_discovered": total_discovered,
            "completed": completed,
            "updated_at": now_iso,
        }
        self._save()

    def clear_checkpoint(self, source_id: str) -> None:
        if source_id in self._checkpoints:
            del self._checkpoints[source_id]
            self._save()


class PaginationController:
    """
    Generic pagination controller that executes page traversal until true source termination.
    """

    def __init__(
        self,
        checkpoint_store: Optional[CrawlCheckpointStore] = None,
        max_pages: Optional[int] = None,
    ):
        self.checkpoints = checkpoint_store or CrawlCheckpointStore()
        self.max_pages = max_pages  # Optional safety ceiling if requested, otherwise unbounded

    def paginate_pages(
        self,
        source_id: str,
        fetch_page_fn: Callable[[int], Tuple[List[Any], bool]],
        start_page: int = 1,
        resume: bool = True,
    ) -> List[Any]:
        """
        Traverses numeric pages (e.g. page=1, 2, 3...) until fetch_page_fn returns has_more=False
        or produces 0 items. Resumes from checkpoint if available.
        fetch_page_fn(page_num) -> (items_list, has_next_page)
        """
        page = start_page
        if resume:
            ckpt = self.checkpoints.get_checkpoint(source_id)
            if ckpt and not ckpt.get("completed", False):
                page = ckpt.get("last_page", start_page)

        all_items: List[Any] = []
        seen_page_hashes: Set[str] = set()

        while True:
            if self.max_pages and page > self.max_pages:
                break

            items, has_more = fetch_page_fn(page)
            if not items:
                # Source termination: empty page
                self.checkpoints.update_checkpoint(source_id, page, total_discovered=len(all_items), completed=True)
                break

            # Check for duplicate page loop
            page_fingerprint = hashlib.sha256(str([str(x) for x in items[:5]]).encode("utf-8")).hexdigest()
            if page_fingerprint in seen_page_hashes:
                # Looping detected; terminate gracefully
                self.checkpoints.update_checkpoint(source_id, page, total_discovered=len(all_items), completed=True)
                break
            seen_page_hashes.add(page_fingerprint)

            all_items.extend(items)
            self.checkpoints.update_checkpoint(source_id, page, total_discovered=len(all_items), completed=not has_more)

            if not has_more:
                break

            page += 1

        return all_items

    def paginate_cursor(
        self,
        source_id: str,
        fetch_cursor_fn: Callable[[Optional[str]], Tuple[List[Any], Optional[str]]],
        initial_cursor: Optional[str] = None,
        resume: bool = True,
    ) -> List[Any]:
        """
        Traverses cursor/token pagination until next_cursor is None or empty.
        fetch_cursor_fn(cursor) -> (items_list, next_cursor)
        """
        cursor = initial_cursor
        if resume:
            ckpt = self.checkpoints.get_checkpoint(source_id)
            if ckpt and not ckpt.get("completed", False):
                cursor = ckpt.get("last_cursor", initial_cursor)

        all_items: List[Any] = []
        page_count = 0

        while True:
            page_count += 1
            if self.max_pages and page_count > self.max_pages:
                break

            items, next_cursor = fetch_cursor_fn(cursor)
            if not items:
                self.checkpoints.update_checkpoint(source_id, page_count, last_cursor=cursor, total_discovered=len(all_items), completed=True)
                break

            all_items.extend(items)
            completed = not bool(next_cursor) or next_cursor == cursor
            self.checkpoints.update_checkpoint(source_id, page_count, last_cursor=next_cursor, total_discovered=len(all_items), completed=completed)

            if completed:
                break

            cursor = next_cursor

        return all_items
