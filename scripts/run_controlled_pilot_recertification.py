#!/usr/bin/env python3
"""
CIVIXAI — CONTROLLED PILOT RE-CERTIFICATION RUNNER
==================================================
Audits and verifies statutory provenance, AST rule completeness,
and governance certification gates for all 27 controlled pilot schemes in the production pool.

Exits with code 0 on SUCCESS, code 1 on invariant violation.
"""
import sys
import json
import sqlite3
from pathlib import Path

# Fix Windows console UTF-8 output if necessary
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CIVIX_DB = PROJECT_ROOT / "data" / "civix.db"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.core.eligibility.production_grade_evaluator import production_eligibility_engine
from services.core.certification.certification_engine import classify_official_source_level


def run_pilot_recertification():
    print("=" * 80)
    print("CIVIXAI CONTROLLED PILOT RE-CERTIFICATION AUDIT")
    print("=" * 80)

    if not CIVIX_DB.exists():
        print(f"[FATAL] Authoritative database missing: {CIVIX_DB}")
        sys.exit(1)

    # 1. Connect to authoritative SQLite DB and retrieve certified citizen schemes
    conn = sqlite3.connect(f"file:{CIVIX_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT DISTINCT s.id, s.canonical_name, s.audience_type, sv.source_url, sv.application_url
        FROM schemes s
        JOIN scheme_versions sv ON s.id = sv.scheme_id
        JOIN scheme_certification_dossiers scd ON s.id = scd.scheme_id
        WHERE s.is_active = 1
          AND s.lifecycle_status = 'ACTIVE'
          AND sv.status = 'published'
          AND scd.semantic_review_status = 'certified'
          AND scd.completeness_status = 'complete'
          AND s.audience_type NOT IN ('INSTITUTIONAL_GRANT', 'NGO_GRANT', 'STATE_OR_LOCAL_BODY_GRANT')
        ORDER BY s.id ASC
    """)
    certified_db_rows = c.fetchall()
    conn.close()

    total_pilots = len(certified_db_rows)
    print(f"Authoritative DB Certified Citizen Pilot Schemes: {total_pilots}")

    if total_pilots != 27:
        print(f"[FAIL] Expected exactly 27 certified citizen pilot schemes, found {total_pilots}")
        sys.exit(1)

    # 2. Audit AST rules, evidence anchors, and source provenance
    verified_count = 0
    anomalies = []

    print("-" * 80)
    print(f"{'#':<3} {'PILOT SCHEME ID':<45} {'TIER':<15} {'RULES':<6} {'STATUS'}")
    print("-" * 80)

    for idx, row in enumerate(certified_db_rows, start=1):
        pid = row["id"]
        pname = row["canonical_name"]
        source_url = row["source_url"] or row["application_url"]

        # Check source level classification
        source_tier = classify_official_source_level(source_url)

        # Check in production eligibility engine
        impl = production_eligibility_engine.implementations.get(pid)
        if not impl:
            anomalies.append(f"{pid}: Missing from production eligibility engine implementations")
            continue

        rules_count = len(impl.get("ast_nodes", []))
        if rules_count == 0:
            anomalies.append(f"{pid}: Zero compiled AST rule nodes")
            continue

        # Invariant: Every AST rule must have an evidence anchor
        missing_anchors = [
            n["fact_key"] for n in impl["ast_nodes"]
            if not n.get("evidence_anchor")
        ]
        if missing_anchors:
            anomalies.append(f"{pid}: Missing evidence anchors for facts: {missing_anchors}")
            continue

        verified_count += 1
        status_label = "CERTIFIED_VALID"
        print(f"{idx:<3} {pid[:43]:<45} {source_tier:<15} {rules_count:<6} {status_label}")

    print("-" * 80)
    print("PILOT AUDIT SUMMARY:")
    print(f"  • Total Pilot Programmes Audited: {total_pilots}")
    print(f"  • Fully Verified Statutory Rules: {verified_count}")
    print(f"  • Sovereign Evidence Anomalies:   {len(anomalies)}")

    if anomalies:
        print("\n[ANOMALIES DETECTED]:")
        for a in anomalies:
            print(f"  [-] {a}")
        sys.exit(1)

    print("\n[SUCCESS] CONTROLLED PILOT RE-CERTIFICATION AUDIT PASSED (100% INVARIANTS SATISFIED)")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(run_pilot_recertification() or 0)
