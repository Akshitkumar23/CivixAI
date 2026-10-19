"""
CIVIXAI — MYSCHEME SOURCE ADAPTER
================================
Authoritative adapter for myScheme national portal and snapshot repository.
Extracts schemes, guidelines, eligibility criteria, benefit summaries, and application routes.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from services.core.discovery.adapters.base import GovernmentProgrammeSource

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SNAPSHOT_DB = PROJECT_ROOT / "data" / "snapshots" / "myscheme_details.db"


class MySchemeAdapter(GovernmentProgrammeSource):
    """
    Adapter for Tier 1: myScheme (National Portal).
    Utilizes local authoritative snapshots (4,208 schemes) and public web entrypoints.
    """

    def __init__(self, source_id: str = "myscheme_portal", config: Optional[Dict[str, Any]] = None):
        super().__init__(source_id=source_id, config=config)
        self.db_path = config.get("snapshot_db", str(SNAPSHOT_DB)) if config else str(SNAPSHOT_DB)

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if not Path(self.db_path).exists():
            return []

        results = []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT slug, scheme_id, status_code, content_hash, raw_json, retrieved_at FROM myscheme_snapshots WHERE status_code = 200"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)

        for row in cursor.fetchall():
            slug = row["slug"]
            scheme_id = row["scheme_id"]
            retrieved_at = row["retrieved_at"]
            raw_data = {}
            if row["raw_json"]:
                try:
                    raw_data = json.loads(row["raw_json"])
                except Exception:
                    pass

            en = raw_data.get("data", {}).get("en", {})
            basic = en.get("basicDetails", {})
            title = basic.get("schemeName") or slug

            results.append({
                "source_id": self.source_id,
                "source_record_id": slug,
                "title": title,
                "raw_payload": raw_data,
                "retrieved_at": retrieved_at,
                "source_url": f"https://www.myscheme.gov.in/schemes/{slug}",
                "source_hash": row["content_hash"] or self.compute_hash(raw_data),
                "source_version": "1.0",
                "http_status": row["status_code"] or 200,
            })
        conn.close()
        return results

    def fetch_detail(self, source_record_id: str) -> Optional[Dict[str, Any]]:
        if not Path(self.db_path).exists():
            return None
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT slug, scheme_id, status_code, raw_json, retrieved_at FROM myscheme_snapshots WHERE slug = ? OR scheme_id = ?",
            (source_record_id, source_record_id)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        data = {}
        if row["raw_json"]:
            try:
                data = json.loads(row["raw_json"])
            except Exception:
                pass
        en = data.get("data", {}).get("en", {})
        basic = en.get("basicDetails", {})
        return {
            "source_id": self.source_id,
            "source_record_id": row["slug"],
            "title": basic.get("schemeName") or row["slug"],
            "raw_payload": data,
            "fetched_at": row["retrieved_at"]
        }

    def fetch_documents(self, source_record_id: str) -> List[Dict[str, Any]]:
        detail = self.fetch_detail(source_record_id)
        if not detail:
            return []
        en = detail.get("raw_payload", {}).get("data", {}).get("en", {})
        content = en.get("schemeContent", {})
        docs = []
        references = content.get("references", [])
        if isinstance(references, list):
            for ref in references:
                if isinstance(ref, dict) and ref.get("url"):
                    docs.append({
                        "title": ref.get("title", "Official Guideline"),
                        "url": ref["url"],
                        "doc_type": "GUIDELINE"
                    })
        return docs

    def fetch_metadata(self) -> Dict[str, Any]:
        count = 0
        if Path(self.db_path).exists():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM myscheme_snapshots WHERE status_code = 200")
            count = cursor.fetchone()[0]
            conn.close()
        return {
            "source_id": self.source_id,
            "tier": "TIER_1_NATIONAL",
            "name": "myScheme National Portal",
            "available_records": count,
            "status": "HEALTHY",
            "access_model": "SNAPSHOT_AND_PUBLIC_PORTAL",
        }

    def health_check(self) -> Dict[str, Any]:
        exists = Path(self.db_path).exists()
        return {
            "source_id": self.source_id,
            "status": "HEALTHY" if exists else "DEGRADED",
            "snapshot_accessible": exists,
            "endpoint": "https://www.myscheme.gov.in"
        }
