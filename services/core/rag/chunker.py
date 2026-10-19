"""
Structure-Aware Document Chunker
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Splits official Government of India scheme documents into semantically coherent,
clause-preserving chunks (eligibility, statutory exclusions, benefit tranches,
document requirements, and application procedures).
"""
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple


class StructureAwareChunker:
    """
    Structure-aware chunker that divides official gazettes, operational guidelines,
    and portal texts into atomic statutory chunks with full provenance metadata.
    Preserves table rows/columns, progressive benefit tranches, nested lists,
    and parent heading context without detaching values.
    """

    @staticmethod
    def compute_chunk_hash(scheme_id: str, section_type: str, heading_path: str, content: str) -> str:
        payload = f"{scheme_id}|{section_type}|{heading_path}|{content.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def format_markdown_table(cls, title: str, headers: List[str], rows: List[List[str]]) -> str:
        """
        Formats structured table data as an authoritative Markdown table.
        """
        if not headers or not rows:
            return ""
        lines = [f"### Table: {title}"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            padded_row = [str(val) for val in row] + [""] * (len(headers) - len(row))
            lines.append("| " + " | ".join(padded_row[:len(headers)]) + " |")
        return "\n".join(lines)

    @classmethod
    def chunk_official_scheme_corpus(
        cls,
        scheme_id: str,
        scheme_name: str,
        scheme_version_id: str,
        document_id: str,
        raw_sections: List[Dict[str, Any]],
        source_url: str,
        source_title: str,
        effective_from: Optional[str] = None,
        effective_to: Optional[str] = None,
        currentness: Optional[str] = "current"
    ) -> List[Dict[str, Any]]:
        """
        Chunks structured official scheme sections into atomic RagChunk specifications.
        Preserves table rows/columns, progressive benefit tranches, nested lists,
        and parent heading context without detaching values.
        """
        chunks = []
        chunk_idx = 0

        for sec in raw_sections:
            heading = sec.get("heading", "General Guidelines")
            heading_path = f"{scheme_name} > {heading}"[:250]
            section_type = sec.get("section_type", "general")
            citation_clause = sec.get("citation_clause") or f"Section: {heading}, {source_title}"
            content_text = sec.get("content", "").strip()
            sec_effective_from = sec.get("effective_from") or effective_from
            sec_effective_to = sec.get("effective_to") or effective_to
            sec_currentness = sec.get("currentness") or currentness or "current"

            # 1. Base Section Chunk (Comprehensive statutory narrative)
            if content_text:
                chunk_idx += 1
                c_id = f"chk-{scheme_id}-{chunk_idx:03d}"
                c_hash = cls.compute_chunk_hash(scheme_id, section_type, heading_path, content_text)

                chunks.append({
                    "id": c_id,
                    "document_id": document_id,
                    "scheme_id": scheme_id,
                    "scheme_version_id": scheme_version_id,
                    "section_type": section_type,
                    "heading_path": heading_path,
                    "content": content_text,
                    "char_length": len(content_text),
                    "token_estimate": len(content_text.split()),
                    "chunk_hash": c_hash,
                    "source_citation": citation_clause,
                    "source_url": source_url,
                    "metadata_json": json.dumps({
                        "scheme_id": scheme_id,
                        "scheme_name": scheme_name,
                        "heading": heading,
                        "section_type": section_type,
                        "source_title": source_title,
                        "structure_type": "statutory_clause",
                        "effective_from": sec_effective_from,
                        "effective_to": sec_effective_to,
                        "currentness": sec_currentness
                    })
                })

            # 2. Structured Tables (Preserving Table Rows & Columns without Detaching Values)
            tables = sec.get("tables", [])
            if isinstance(tables, list):
                for tbl in tables:
                    tbl_title = tbl.get("title", f"{heading} Schedule Table")
                    headers = [str(h) for h in tbl.get("headers", [])]
                    rows = tbl.get("rows", [])
                    tbl_clause = tbl.get("citation_clause") or citation_clause
                    tbl_heading_path = f"{scheme_name} > {heading} > {tbl_title}"[:250]

                    if not headers or not rows:
                        continue

                    # If table is <= 15 rows, format as a complete structured table chunk preserving all rows & columns
                    # If larger, split into row-batches repeating column headers so values are never detached
                    batch_size = 15
                    for batch_start in range(0, len(rows), batch_size):
                        batch_rows = rows[batch_start:batch_start + batch_size]
                        batch_suffix = f" (Part {batch_start // batch_size + 1})" if len(rows) > batch_size else ""
                        batch_title = f"{tbl_title}{batch_suffix}"
                        batch_heading_path = f"{scheme_name} > {heading} > {batch_title}"[:250]
                        md_table = cls.format_markdown_table(batch_title, headers, batch_rows)

                        chunk_idx += 1
                        c_id = f"chk-{scheme_id}-{chunk_idx:03d}"
                        c_hash = cls.compute_chunk_hash(scheme_id, section_type, batch_heading_path, md_table)

                        chunks.append({
                            "id": c_id,
                            "document_id": document_id,
                            "scheme_id": scheme_id,
                            "scheme_version_id": scheme_version_id,
                            "section_type": section_type,
                            "heading_path": batch_heading_path,
                            "content": md_table,
                            "char_length": len(md_table),
                            "token_estimate": len(md_table.split()),
                            "chunk_hash": c_hash,
                            "source_citation": tbl_clause,
                            "source_url": source_url,
                            "metadata_json": json.dumps({
                                "scheme_id": scheme_id,
                                "scheme_name": scheme_name,
                                "heading": heading,
                                "table_title": batch_title,
                                "section_type": section_type,
                                "source_title": source_title,
                                "structure_type": "table_full",
                                "headers": headers,
                                "rows_count": len(batch_rows),
                                "effective_from": sec_effective_from,
                                "effective_to": sec_effective_to,
                                "currentness": sec_currentness
                            })
                        })

            # 3. Progressive Benefit Tranches (Preserving Complete Progressive Tranche Sequence, Amounts & Tenures)
            tranches = sec.get("tranches", [])
            if isinstance(tranches, list) and tranches:
                t_heading_path = f"{scheme_name} > {heading} > Progressive Tranches Schedule"[:250]
                t_clause = tranches[0].get("citation_clause") or citation_clause

                tranche_lines = [
                    f"[{scheme_name} > {heading} > Progressive Tranches Schedule]"
                ]
                for t_idx, tr in enumerate(tranches):
                    t_name = tr.get("tranche_name", f"Tranche {t_idx + 1}")
                    amount = tr.get("amount", "")
                    tenure = tr.get("tenure", "")
                    conditions = tr.get("conditions", "")
                    tranche_lines.append(
                        f"• {t_name}: Progressive Loan / Benefit Amount: {amount} | Repayment Tenure: {tenure} | Conditions: {conditions}"
                    )

                t_content = "\n".join(tranche_lines)
                chunk_idx += 1
                c_id = f"chk-{scheme_id}-{chunk_idx:03d}"
                c_hash = cls.compute_chunk_hash(scheme_id, section_type, t_heading_path, t_content)

                chunks.append({
                    "id": c_id,
                    "document_id": document_id,
                    "scheme_id": scheme_id,
                    "scheme_version_id": scheme_version_id,
                    "section_type": section_type,
                    "heading_path": t_heading_path,
                    "content": t_content,
                    "char_length": len(t_content),
                    "token_estimate": len(t_content.split()),
                    "chunk_hash": c_hash,
                    "source_citation": t_clause,
                    "source_url": source_url,
                    "metadata_json": json.dumps({
                        "scheme_id": scheme_id,
                        "scheme_name": scheme_name,
                        "heading": heading,
                        "section_type": section_type,
                        "source_title": source_title,
                        "structure_type": "progressive_tranches_schedule",
                        "tranches_count": len(tranches),
                        "effective_from": sec_effective_from,
                        "effective_to": sec_effective_to,
                        "currentness": sec_currentness
                    })
                })

            # 4. Nested Lists (Preserving Hierarchical Item & Exclusion Context)
            nested_items = sec.get("nested_items", [])
            if isinstance(nested_items, list):
                for grp in nested_items:
                    grp_title = grp.get("item_title", heading)
                    items = grp.get("items", [])
                    grp_clause = grp.get("citation_clause") or citation_clause
                    grp_heading_path = f"{scheme_name} > {heading} > {grp_title}"[:250]

                    if not items:
                        continue

                    grp_content = (
                        f"[{scheme_name} > {heading} > {grp_title}]\n" +
                        "\n".join([f"• {it}" for it in items])
                    )

                    chunk_idx += 1
                    c_id = f"chk-{scheme_id}-{chunk_idx:03d}"
                    c_hash = cls.compute_chunk_hash(scheme_id, section_type, grp_heading_path, grp_content)

                    chunks.append({
                        "id": c_id,
                        "document_id": document_id,
                        "scheme_id": scheme_id,
                        "scheme_version_id": scheme_version_id,
                        "section_type": section_type,
                        "heading_path": grp_heading_path,
                        "content": grp_content,
                        "char_length": len(grp_content),
                        "token_estimate": len(grp_content.split()),
                        "chunk_hash": c_hash,
                        "source_citation": grp_clause,
                        "source_url": source_url,
                        "metadata_json": json.dumps({
                            "scheme_id": scheme_id,
                            "scheme_name": scheme_name,
                            "heading": heading,
                            "item_title": grp_title,
                            "section_type": section_type,
                            "source_title": source_title,
                            "structure_type": "nested_list",
                            "items_count": len(items),
                            "effective_from": sec_effective_from,
                            "effective_to": sec_effective_to,
                            "currentness": sec_currentness
                        })
                    })

            # 5. Backward-Compatible Sub-Items
            sub_items = sec.get("sub_items", [])
            if sub_items:
                for item in sub_items:
                    item_heading = item.get("sub_heading", heading)
                    item_heading_path = f"{scheme_name} > {heading} > {item_heading}"[:250]
                    item_content = item.get("content", "").strip()
                    item_clause = item.get("citation_clause") or citation_clause

                    if not item_content:
                        continue

                    chunk_idx += 1
                    c_id = f"chk-{scheme_id}-{chunk_idx:03d}"
                    c_hash = cls.compute_chunk_hash(scheme_id, section_type, item_heading_path, item_content)

                    chunks.append({
                        "id": c_id,
                        "document_id": document_id,
                        "scheme_id": scheme_id,
                        "scheme_version_id": scheme_version_id,
                        "section_type": section_type,
                        "heading_path": item_heading_path,
                        "content": item_content,
                        "char_length": len(item_content),
                        "token_estimate": len(item_content.split()),
                        "chunk_hash": c_hash,
                        "source_citation": item_clause,
                        "source_url": source_url,
                        "metadata_json": json.dumps({
                            "scheme_id": scheme_id,
                            "scheme_name": scheme_name,
                            "heading": heading,
                            "sub_heading": item_heading,
                            "section_type": section_type,
                            "source_title": source_title,
                            "structure_type": "sub_item",
                            "effective_from": sec_effective_from,
                            "effective_to": sec_effective_to,
                            "currentness": sec_currentness
                        })
                    })

        return chunks
