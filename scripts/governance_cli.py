"""
CIVIXAI — SECURE HUMAN GOVERNANCE CLI TOOL
===========================================
Interactive, secure command-line interface for authorized human reviewers
to inspect, evaluate, and record governance decisions on TIER-4 review packets.

Commands:
  python scripts/governance_cli.py list
  python scripts/governance_cli.py view <scheme_id>
  python scripts/governance_cli.py decide <scheme_id> --decision APPROVE --reviewer-id <id> --reviewer-role <role> --citation <citation>
  python scripts/governance_cli.py certify <scheme_id> --reviewer-id <id> --reviewer-role <role>

Strict Invariants:
- Requires authenticated human reviewer identity and approved role.
- Synthetic, automated, or bot reviewers are strictly rejected.
"""

import sys
import argparse
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.governance.engine import (
    GovernanceEngine, UnauthorizedReviewerError, InvalidDecisionError,
    InvalidStateTransitionError, CertificationGateError, ALLOWED_DECISIONS, ALLOWED_ROLES
)

PACKETS_DIR = PROJECT_ROOT / 'data' / 'governance' / 'review_packets'

def cmd_list(args):
    engine = GovernanceEngine()
    packet_files = sorted(list(PACKETS_DIR.glob('*.json')))
    print("=" * 85)
    print(f"CIVIXAI HUMAN GOVERNANCE REVIEW QUEUE — TOTAL CANDIDATES: {len(packet_files)}")
    print("=" * 85)
    print(f"{'#':<4} {'SCHEME ID':<45} {'STATUS':<20} {'CRITERIA':<8}")
    print("-" * 85)

    status_counts = {}
    for idx, pf in enumerate(packet_files, start=1):
        with open(pf, 'r', encoding='utf-8') as f:
            pkt = json.load(f)
        sid = pkt['section_a_scheme_identity']['scheme_id']
        st = pkt.get('governance_status', 'REVIEW_REQUIRED')
        crit_len = len(pkt.get('section_e_structured_criteria', []))
        status_counts[st] = status_counts.get(st, 0) + 1
        print(f"{idx:<4} {sid[:43]:<45} {st:<20} {crit_len:<8}")

    print("-" * 85)
    print("QUEUE SUMMARY:")
    for st, count in sorted(status_counts.items()):
        print(f"  {st:25s}: {count}")
    print("=" * 85)

def cmd_view(args):
    engine = GovernanceEngine()
    try:
        pkt = engine.load_packet(args.scheme_id)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    ident = pkt['section_a_scheme_identity']
    src = pkt['section_b_official_source']
    snap = pkt['section_c_snapshot_integrity']
    print("=" * 85)
    print(f"IMMUTABLE GOVERNANCE REVIEW PACKET: {ident['scheme_id']}")
    print("=" * 85)
    print(f"Scheme Name   : {ident['canonical_name']}")
    print(f"Programme Kind: {ident['programme_type']} | Audience: {ident['audience_type']}")
    print(f"Official Source: {src['source_url']} ({src['source_type']})")
    print(f"Snapshot Hash : {snap['source_hash']} (Retrieved: {snap['retrieved_at']})")
    print(f"Current State : {pkt.get('governance_status')}")

    print("\n--- SECTION D: EXACT ELIGIBILITY SOURCE TEXT ---")
    print(pkt.get('section_d_exact_eligibility_text', '')[:1000])

    print("\n--- SECTION E: STRUCTURED CANONICAL CRITERIA ---")
    for idx, c in enumerate(pkt.get('section_e_structured_criteria', []), start=1):
        print(f"  [{idx}] {c['fact_key']} {c['operator']} {c['expected_value']}")
        print(f"      Source fragment: \"{c.get('evidence_fragment', '')}\"")

    print("\n--- SECTION F: STATUTORY EXCLUSIONS ---")
    ex = pkt.get('section_f_exclusions', {})
    print(f"  Count: {ex.get('exclusion_count', 0)}")
    print(f"  Text : {ex.get('exclusions_text', '')[:400]}")

    print("\n--- SECTION H: COMPILED AST ---")
    print(json.dumps(pkt.get('section_h_ast', {}), indent=2))

    print("\n--- SECTION O: REVIEWER CHECKLIST (22 MANDATORY QUESTIONS) ---")
    for q in pkt.get('section_o_reviewer_checklist', []):
        print(f"  [Q{q['question_id']:02d}] {q['question']:<50} -> {q['answer']}")

    dec = pkt.get('section_p_governance_decision', {})
    print("\n--- SECTION P: GOVERNANCE DECISION ---")
    print(f"  Decision   : {dec.get('decision')}")
    print(f"  Reviewer   : {dec.get('reviewer_id')} ({dec.get('reviewer_role')})")
    print(f"  Certified  : {dec.get('certified')}")
    print(f"  Ready Flag : {dec.get('eligibility_ready')}")
    print("=" * 85)

def cmd_decide(args):
    engine = GovernanceEngine()
    try:
        updated = engine.record_decision(
            scheme_id=args.scheme_id,
            decision=args.decision,
            reviewer_id=args.reviewer_id,
            reviewer_role=args.reviewer_role,
            citation=args.citation,
            notes=args.notes or ""
        )
        print("=" * 70)
        print(f"SUCCESS: Decision '{args.decision}' successfully recorded!")
        print(f"Scheme ID    : {args.scheme_id}")
        print(f"New Status   : {updated['governance_status']}")
        print(f"Reviewer ID  : {args.reviewer_id} ({args.reviewer_role})")
        print(f"Certified    : {updated['section_p_governance_decision']['certified']}")
        print(f"EligibleReady: {updated['section_p_governance_decision']['eligibility_ready']}")
        print("=" * 70)
    except Exception as e:
        print(f"GOVERNANCE VIOLATION: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_certify(args):
    engine = GovernanceEngine()
    try:
        updated = engine.certify_scheme(
            scheme_id=args.scheme_id,
            reviewer_id=args.reviewer_id,
            reviewer_role=args.reviewer_role
        )
        print("=" * 70)
        print(f"SUCCESS: Scheme '{args.scheme_id}' passed Certification Gate!")
        print(f"New Status   : {updated['governance_status']}")
        print(f"Certified    : {updated['section_p_governance_decision']['certified']}")
        print("=" * 70)
    except Exception as e:
        print(f"CERTIFICATION GATE BLOCKED: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="CivixAI Human Governance Review CLI")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List all pending review packets")
    p_list.set_defaults(func=cmd_list)

    # view
    p_view = subparsers.add_parser("view", help="View full immutable review packet")
    p_view.add_argument("scheme_id", type=str, help="Canonical scheme ID")
    p_view.set_defaults(func=cmd_view)

    # decide
    p_decide = subparsers.add_parser("decide", help="Record an authentic human governance decision")
    p_decide.add_argument("scheme_id", type=str, help="Canonical scheme ID")
    p_decide.add_argument("--decision", type=str, required=True, choices=list(ALLOWED_DECISIONS))
    p_decide.add_argument("--reviewer-id", type=str, required=True, help="Authenticated reviewer ID")
    p_decide.add_argument("--reviewer-role", type=str, required=True, choices=list(ALLOWED_ROLES))
    p_decide.add_argument("--citation", type=str, required=True, help="Official statutory citation")
    p_decide.add_argument("--notes", type=str, default="", help="Review notes")
    p_decide.set_defaults(func=cmd_decide)

    # certify
    p_certify = subparsers.add_parser("certify", help="Execute the statutory certification gate")
    p_certify.add_argument("scheme_id", type=str, help="Canonical scheme ID")
    p_certify.add_argument("--reviewer-id", type=str, required=True)
    p_certify.add_argument("--reviewer-role", type=str, required=True, choices=list(ALLOWED_ROLES))
    p_certify.set_defaults(func=cmd_certify)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
