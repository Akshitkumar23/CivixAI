"""
Program Candidate & Canonical Exporter
======================================
Generates downstream CSV artifacts for discovered government candidates, private
candidates, and authoritative canonical programs.
CRITICAL INVARIANT: CSV files are downstream exports ONLY, never the source of truth.
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from services.core.discovery.models import ProgramCandidate
from services.core.database.models import Scheme, SchemeVersion


GOV_CANDIDATE_COLUMNS = [
    "candidate_id",
    "program_type",
    "sector",
    "provider_type",
    "provider_name",
    "official_name",
    "source_url",
    "source_domain",
    "source_id",
    "authority_tier",
    "discovery_method",
    "discovery_timestamp",
    "content_hash",
    "identity_key",
    "possible_duplicate_of",
    "discovery_status",
    "verification_status",
    "governance_status",
    "eligibility_summary",
    "benefit_summary",
]

PRIVATE_CANDIDATE_COLUMNS = [
    "candidate_id",
    "product_type",
    "sector",
    "provider_type",
    "provider_name",
    "official_name",
    "official_url",
    "source_domain",
    "source_id",
    "authority_tier",
    "source_timestamp",
    "content_hash",
    "identity_key",
    "possible_duplicate_of",
    "regulatory_framework",
    "availability_status",
    "verification_status",
    "eligibility_summary",
    "benefit_summary",
]

CANONICAL_PROGRAM_COLUMNS = [
    "scheme_id",
    "canonical_name",
    "scheme_level",
    "authority_name",
    "version_number",
    "status",
    "source_url",
    "last_reviewed_at",
]


class ProgramCandidateExporter:
    """
    Exports discovered candidates and canonical schemes to downstream CSV / JSONL artifacts.
    """

    @staticmethod
    def stage_candidates_jsonl(candidates: List[ProgramCandidate], filepath: str) -> int:
        """
        Saves candidate records into an appendable JSONL staging file.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(path, "w", encoding="utf-8") as f:
            for cand in candidates:
                f.write(json.dumps(cand.to_dict(), ensure_ascii=False) + "\n")
                count += 1
        return count

    @staticmethod
    def export_candidates_csv(
        candidates: List[ProgramCandidate],
        gov_csv_path: str = "data/exports/government_program_candidates.csv",
        private_csv_path: str = "data/exports/private_program_candidates.csv",
    ) -> Dict[str, int]:
        """
        Exports staged candidates to separate Government and Private CSV artifacts.
        Strictly segregates government schemes from private financial products.
        """
        gov_path = Path(gov_csv_path)
        gov_path.parent.mkdir(parents=True, exist_ok=True)
        priv_path = Path(private_csv_path)
        priv_path.parent.mkdir(parents=True, exist_ok=True)

        gov_count = 0
        priv_count = 0

        # Government CSV
        with open(gov_path, "w", newline="", encoding="utf-8") as f_gov:
            writer = csv.writer(f_gov)
            writer.writerow(GOV_CANDIDATE_COLUMNS)
            for c in candidates:
                if c.is_government():
                    writer.writerow([
                        c.candidate_id,
                        c.program_type,
                        c.sector,
                        c.provider_type,
                        c.provider_name,
                        c.official_name,
                        c.source_url,
                        c.source_domain,
                        c.source_id,
                        c.authority_tier,
                        c.discovery_method,
                        c.discovery_timestamp,
                        c.content_hash,
                        c.identity_key,
                        ";".join(c.possible_duplicate_of) if c.possible_duplicate_of else "",
                        c.discovery_status,
                        c.verification_status,
                        c.governance_status,
                        c.eligibility_summary,
                        c.benefit_summary,
                    ])
                    gov_count += 1

        # Private CSV
        with open(priv_path, "w", newline="", encoding="utf-8") as f_priv:
            writer = csv.writer(f_priv)
            writer.writerow(PRIVATE_CANDIDATE_COLUMNS)
            for c in candidates:
                if c.is_private():
                    reg_framework = c.raw_metadata.get("regulatory_framework", "Regulated Financial Institution")
                    avail = c.raw_metadata.get("availability_status", "active")
                    writer.writerow([
                        c.candidate_id,
                        c.program_type,
                        c.sector,
                        c.provider_type,
                        c.provider_name,
                        c.official_name,
                        c.source_url,
                        c.source_domain,
                        c.source_id,
                        c.authority_tier,
                        c.discovery_timestamp,
                        c.content_hash,
                        c.identity_key,
                        ";".join(c.possible_duplicate_of) if c.possible_duplicate_of else "",
                        reg_framework,
                        avail,
                        c.verification_status,
                        c.eligibility_summary,
                        c.benefit_summary,
                    ])
                    priv_count += 1

        return {"government_exported": gov_count, "private_exported": priv_count}

    @staticmethod
    def export_canonical_programs(
        db: Session,
        canonical_csv_path: str = "data/exports/canonical_programs.csv",
    ) -> int:
        """
        Exports currently published canonical programs from the production DB.
        DB is the runtime source of truth; CSV is downstream only.
        """
        canon_path = Path(canonical_csv_path)
        canon_path.parent.mkdir(parents=True, exist_ok=True)

        schemes = db.query(Scheme).all()
        count = 0
        with open(canon_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CANONICAL_PROGRAM_COLUMNS)
            for s in schemes:
                latest_v = db.query(SchemeVersion).filter(
                    SchemeVersion.scheme_id == s.id
                ).order_by(SchemeVersion.version_number.desc()).first()

                writer.writerow([
                    s.id,
                    s.canonical_name,
                    s.scheme_level,
                    s.authority.name if s.authority else "",
                    latest_v.version_number if latest_v else 0,
                    latest_v.status if latest_v else "unknown",
                    latest_v.source_url if latest_v else "",
                    latest_v.published_at.isoformat() if latest_v and latest_v.published_at else "",
                ])
                count += 1
        return count
