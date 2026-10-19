"""
SQLite FTS5 Full-Text Search Manager
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Manages the SQLite FTS5 virtual table `rag_chunks_fts`, providing BM25 scoring,
Unicode61 tokenization (supporting Devanagari Hindi and English), and index sync.
"""
import re
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class FtsManager:
    """
    Interface for SQLite FTS5 virtual table indexing and BM25 lexical querying.
    """

    TABLE_NAME = "rag_chunks_fts"

    def __init__(self, db_connection_or_path: Any):
        from pathlib import Path
        if isinstance(db_connection_or_path, (str, Path)):
            self.conn = sqlite3.connect(str(db_connection_or_path), check_same_thread=False)
            self._owns_conn = True
        elif hasattr(db_connection_or_path, "driver_connection"):
            self.conn = db_connection_or_path.driver_connection
            self._owns_conn = False
        elif hasattr(db_connection_or_path, "connection"):
            conn_obj = db_connection_or_path.connection
            if hasattr(conn_obj, "driver_connection"):
                self.conn = conn_obj.driver_connection
            elif hasattr(conn_obj, "dbapi_connection") and conn_obj.dbapi_connection is not None:
                self.conn = conn_obj.dbapi_connection
            else:
                self.conn = conn_obj
            self._owns_conn = False
        elif hasattr(db_connection_or_path, "raw_connection"):
            raw = db_connection_or_path.raw_connection()
            self.conn = getattr(raw, "driver_connection", getattr(raw, "dbapi_connection", raw))
            self._owns_conn = False
        else:
            self.conn = db_connection_or_path
            self._owns_conn = False

    def ensure_table(self):
        cursor = self.conn.cursor()
        cols = [c[1] for c in cursor.execute(f"PRAGMA table_info({self.TABLE_NAME})").fetchall()]
        if not cols:
            cursor.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.TABLE_NAME} USING fts5(
                chunk_id UNINDEXED,
                content,
                heading_path,
                section_type,
                scheme_id,
                generation_id UNINDEXED,
                is_active UNINDEXED,
                tokenize='unicode61'
            )
            """)
            self.conn.commit()
        elif "generation_id" not in cols:
            rows = cursor.execute(f"SELECT chunk_id, content, heading_path, section_type, scheme_id FROM {self.TABLE_NAME}").fetchall()
            cursor.execute(f"DROP TABLE {self.TABLE_NAME}")
            cursor.execute(f"""
            CREATE VIRTUAL TABLE {self.TABLE_NAME} USING fts5(
                chunk_id UNINDEXED,
                content,
                heading_path,
                section_type,
                scheme_id,
                generation_id UNINDEXED,
                is_active UNINDEXED,
                tokenize='unicode61'
            )
            """)
            for r in rows:
                cursor.execute(
                    f"INSERT INTO {self.TABLE_NAME} (chunk_id, content, heading_path, section_type, scheme_id, generation_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (r[0], r[1], r[2], r[3], r[4], "gen-legacy", 1)
                )
            self.conn.commit()

    def sanitize_fts_query(self, query: str) -> str:
        """
        Sanitizes user input into a valid FTS5 MATCH expression.
        Strips SQLite FTS syntax characters (*, ^, :, ", (, ), etc.)
        and forms an OR / phrase combination.
        """
        # Remove FTS5 operator characters
        cleaned = re.sub(r'[\*\^\:\(\)\"\{\}\+\-\~]', ' ', query)
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 0]
        if not tokens:
            return ""

        # Construct boolean OR expression across tokens for broad recall
        # Wrap individual tokens in double quotes to prevent syntax errors
        safe_tokens = [f'"{t}"' for t in tokens]
        match_expr = " OR ".join(safe_tokens)
        return match_expr

    def insert_chunk(
        self,
        chunk_id: str,
        content: str,
        heading_path: str,
        section_type: str,
        scheme_id: str,
        generation_id: Optional[str] = "default",
        is_active: bool = True
    ):
        cursor = self.conn.cursor()
        cursor.execute(f"""
        INSERT INTO {self.TABLE_NAME} (chunk_id, content, heading_path, section_type, scheme_id, generation_id, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chunk_id, content, heading_path, section_type, scheme_id, generation_id or "default", 1 if is_active else 0))
        self.conn.commit()

    def bulk_insert_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        cursor = self.conn.cursor()
        formatted = [
            {
                "chunk_id": c["chunk_id"],
                "content": c["content"],
                "heading_path": c.get("heading_path", ""),
                "section_type": c.get("section_type", "general"),
                "scheme_id": c.get("scheme_id", ""),
                "generation_id": c.get("generation_id", "default") or "default",
                "is_active": 1 if c.get("is_active", True) else 0
            }
            for c in chunks
        ]
        cursor.executemany(f"""
        INSERT INTO {self.TABLE_NAME} (chunk_id, content, heading_path, section_type, scheme_id, generation_id, is_active)
        VALUES (:chunk_id, :content, :heading_path, :section_type, :scheme_id, :generation_id, :is_active)
        """, formatted)
        self.conn.commit()

    def activate_generation(self, generation_id: str, deactivate_others: bool = True):
        cursor = self.conn.cursor()
        if deactivate_others:
            cursor.execute(f"UPDATE {self.TABLE_NAME} SET is_active = 0 WHERE is_active = 1")
        cursor.execute(f"UPDATE {self.TABLE_NAME} SET is_active = 1 WHERE generation_id = ?", (generation_id,))
        self.conn.commit()

    def deactivate_generation(self, generation_id: str):
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE {self.TABLE_NAME} SET is_active = 0 WHERE generation_id = ?", (generation_id,))
        self.conn.commit()

    def delete_generation(self, generation_id: str):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE generation_id = ?", (generation_id,))
        self.conn.commit()

    def rollback_to_generation(self, generation_id: str):
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE {self.TABLE_NAME} SET is_active = 0 WHERE is_active = 1")
        cursor.execute(f"UPDATE {self.TABLE_NAME} SET is_active = 1 WHERE generation_id = ?", (generation_id,))
        self.conn.commit()

    def delete_chunks_for_scheme(self, scheme_id: str):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE scheme_id = ?", (scheme_id,))
        self.conn.commit()

    def clear_all(self):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.TABLE_NAME}")
        self.conn.commit()

    def search(
        self,
        query: str,
        scheme_id_filter: Optional[Union[str, Set[str], List[str], Tuple[str, ...]]] = None,
        generation_id: Optional[str] = None,
        active_only: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes BM25 full-text search against rag_chunks_fts.
        Returns chunk_id, bm25_score (higher is better), and matched fields.
        """
        match_expr = self.sanitize_fts_query(query)
        if not match_expr:
            return []

        cursor = self.conn.cursor()
        where_clauses = [f"{self.TABLE_NAME} MATCH ?"]
        params: List[Any] = [match_expr]

        if scheme_id_filter:
            if isinstance(scheme_id_filter, (set, list, tuple)):
                if scheme_id_filter:
                    placeholders = ",".join(["?"] * len(scheme_id_filter))
                    where_clauses.append(f"scheme_id IN ({placeholders})")
                    params.extend(list(scheme_id_filter))
            else:
                where_clauses.append("scheme_id = ?")
                params.append(scheme_id_filter)


        if generation_id:
            where_clauses.append("generation_id = ?")
            params.append(generation_id)
        elif active_only:
            where_clauses.append("is_active = 1")

        sql = f"""
        SELECT chunk_id, bm25({self.TABLE_NAME}) as raw_bm25, heading_path, section_type, scheme_id
        FROM {self.TABLE_NAME}
        WHERE {" AND ".join(where_clauses)}
        ORDER BY raw_bm25 ASC
        LIMIT ?
        """
        params.append(limit)
        cursor.execute(sql, tuple(params))

        rows = cursor.fetchall()
        results = []
        for r in rows:
            # SQLite bm25 returns negative values where more negative = higher relevance
            # Convert to positive score: -raw_bm25
            raw_bm25 = r[1]
            relevance_score = -float(raw_bm25) if raw_bm25 is not None else 0.0
            results.append({
                "chunk_id": r[0],
                "bm25_score": relevance_score,
                "heading_path": r[2],
                "section_type": r[3],
                "scheme_id": r[4]
            })
        return results

    def close(self):
        if self._owns_conn and self.conn:
            self.conn.close()
