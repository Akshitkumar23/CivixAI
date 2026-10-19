"""
Deterministic Data Quality Engine
Enforces 12 data quality rules on scheme versions, sources, and draft changesets.
Critical failures strictly block human publication.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json

from services.core.facts import FACT_CATALOGUE
from services.core.database.models import SchemeVersion, SourceRegistry, SchemeChangeSet

class QualityViolation:
    def __init__(self, code: str, severity: str, message: str, field: Optional[str] = None):
        self.code = code
        self.severity = severity # CRITICAL, WARNING, INFO
        self.message = message
        self.field = field

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "field": self.field or ""
        }

class QualityReport:
    def __init__(self, violations: List[QualityViolation]):
        self.violations = violations
        self.critical_errors = [v for v in violations if v.severity == "CRITICAL"]
        self.warnings = [v for v in violations if v.severity == "WARNING"]
        self.info = [v for v in violations if v.severity == "INFO"]
        self.is_valid_for_publication = len(self.critical_errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid_for_publication": self.is_valid_for_publication,
            "critical_count": len(self.critical_errors),
            "warning_count": len(self.warnings),
            "violations": [v.to_dict() for v in self.violations]
        }

class DataQualityEngine:
    @classmethod
    def audit_changeset(
        cls,
        changeset: SchemeChangeSet,
        source: Optional[SourceRegistry] = None
    ) -> QualityReport:
        violations: List[QualityViolation] = []

        # 1. Source URL validity
        if source:
            if not source.canonical_url:
                violations.append(QualityViolation("MISSING_OFFICIAL_URL", "CRITICAL", "Source is missing canonical URL", "canonical_url"))
            elif not any(d in source.canonical_url for d in [".gov.in", ".nic.in", "egazette"]):
                violations.append(QualityViolation("NON_GOVERNMENT_URL", "WARNING", f"Source '{source.canonical_url}' does not use official .gov.in/.nic.in domain", "canonical_url"))

            # 2. Publisher presence
            if not source.publisher or source.publisher.strip() == "":
                violations.append(QualityViolation("MISSING_PUBLISHER", "WARNING", "Source document publisher is not specified", "publisher"))

            # 2b. Parser Health & OCR check
            p_health = getattr(source, "parser_health", "complete")
            if p_health == "ocr_required":
                violations.append(QualityViolation("OCR_REQUIRED_DOCUMENT", "CRITICAL", "Source is a scanned image PDF requiring OCR; text extraction is incomplete", "parser_health"))
            elif p_health == "failed":
                violations.append(QualityViolation("PARSER_FAILED_DOCUMENT", "CRITICAL", "Source document parsing failed completely; cannot certify rules", "parser_health"))

        # 3. Rule checks
        rule_drafts = changeset.rule_drafts
        seen_rules = set()

        for r in rule_drafts:
            # Check fact key in catalog
            if r.fact_key not in FACT_CATALOGUE:
                violations.append(QualityViolation(
                    "UNKNOWN_FACT_KEY", "CRITICAL",
                    f"Rule references fact key '{r.fact_key}' not registered in canonical FACT_CATALOGUE",
                    f"rule.{r.fact_key}"
                ))

            # Check rule evidence fragment
            if not r.source_fragment or r.source_fragment.strip() == "":
                violations.append(QualityViolation(
                    "RULE_WITHOUT_EVIDENCE", "CRITICAL",
                    f"Rule for '{r.fact_key}' lacks mandatory source evidence fragment citation",
                    f"rule.{r.fact_key}"
                ))

            # Duplicate rule check
            rule_sig = (r.fact_key, r.operator, r.expected_value)
            if rule_sig in seen_rules:
                violations.append(QualityViolation(
                    "DUPLICATE_RULE", "WARNING",
                    f"Duplicate rule detected for fact '{r.fact_key}' with value '{r.expected_value}'",
                    f"rule.{r.fact_key}"
                ))
            seen_rules.add(rule_sig)

            # Numeric/range sanity
            if r.operator == "between":
                try:
                    vals = json.loads(r.expected_value.replace("'", '"'))
                    if isinstance(vals, list) and len(vals) == 2:
                        if vals[0] > vals[1]:
                            violations.append(QualityViolation(
                                "IMPOSSIBLE_NUMERIC_RANGE", "CRITICAL",
                                f"Invalid between range for '{r.fact_key}': min ({vals[0]}) > max ({vals[1]})",
                                f"rule.{r.fact_key}"
                            ))
                except Exception:
                    pass

        # 4. Document requirement evidence
        for d in changeset.document_drafts:
            if not d.source_fragment or d.source_fragment.strip() == "":
                violations.append(QualityViolation(
                    "DOCUMENT_WITHOUT_EVIDENCE", "WARNING",
                    f"Document requirement '{d.document_type}' lacks cited source fragment",
                    f"document.{d.document_type}"
                ))

        # 5. Benefit evidence
        for b in changeset.benefit_drafts:
            if not b.source_fragment or b.source_fragment.strip() == "":
                violations.append(QualityViolation(
                    "BENEFIT_WITHOUT_EVIDENCE", "WARNING",
                    f"Benefit description lacks cited source fragment",
                    "benefit"
                ))

        return QualityReport(violations)

    @classmethod
    def audit_scheme_version(cls, version: SchemeVersion) -> QualityReport:
        """Audits an existing production scheme version for data health."""
        violations: List[QualityViolation] = []

        if not version.source_url:
            violations.append(QualityViolation("MISSING_OFFICIAL_URL", "WARNING", "Production version lacks official source URL", "source_url"))

        if not version.effective_from:
            violations.append(QualityViolation("MISSING_EFFECTIVE_DATE", "INFO", "Scheme version has no effective start date", "effective_from"))

        if version.effective_from and version.effective_to and version.effective_from > version.effective_to:
            violations.append(QualityViolation("INVALID_DATE_RANGE", "CRITICAL", "effective_from is after effective_to", "effective_dates"))

        for r in version.rules:
            if r.fact_key not in FACT_CATALOGUE:
                violations.append(QualityViolation("UNKNOWN_FACT_KEY", "CRITICAL", f"Rule uses unknown fact '{r.fact_key}'", f"rule.{r.id}"))
            if not r.source_fragment and getattr(r, "verification_status", "") == "source_verified":
                violations.append(QualityViolation("VERIFIED_WITHOUT_EVIDENCE", "CRITICAL", f"Rule marked source_verified without source fragment citation", f"rule.{r.id}"))

        return QualityReport(violations)
