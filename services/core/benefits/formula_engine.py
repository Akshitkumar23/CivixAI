"""
CivixAI Benefit Formula Engine
==============================
Extracts and computes deterministic welfare entitlements from statutory benefit
summaries, strictly decoupled from legal eligibility logic.

Supported Entitlement Types:
- CASH_TRANSFER (e.g., Direct Benefit Transfer ₹6,000/yr in 3 installments)
- IN_KIND_SUBSIDY (e.g., Subsidized food grains, agricultural implements)
- CREDIT_LOAN (e.g., Collateral-free loan up to ₹10 Lakhs, interest subvention)
- INSURANCE_COVER (e.g., Life cover ₹2 Lakhs, Health cover ₹5 Lakhs)
- SCHOLARSHIP_EDUCATION (e.g., Tuition reimbursement + maintenance allowance)
- SERVICE_EMERGENCY (e.g., Free 24x7 108 emergency ambulance transport)
"""

from __future__ import annotations
import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.core.discovery.governance import EvidenceAnchor


class BenefitType(str, Enum):
    CASH_TRANSFER = "CASH_TRANSFER"
    IN_KIND_SUBSIDY = "IN_KIND_SUBSIDY"
    CREDIT_LOAN = "CREDIT_LOAN"
    INSURANCE_COVER = "INSURANCE_COVER"
    SCHOLARSHIP_EDUCATION = "SCHOLARSHIP_EDUCATION"
    SERVICE_EMERGENCY = "SERVICE_EMERGENCY"
    MISCELLANEOUS = "MISCELLANEOUS"


class PaymentCadence(str, Enum):
    ONE_TIME = "ONE_TIME"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"
    ON_EVENT = "ON_EVENT"  # e.g. admission, hospitalization, accident
    CONTINUOUS = "CONTINUOUS"


class BenefitFormula(BaseModel):
    benefit_id: str
    candidate_id: str
    benefit_type: BenefitType
    cadence: PaymentCadence = PaymentCadence.ON_EVENT
    nominal_amount: Optional[float] = None
    currency: str = "INR"
    benefit_description: str
    formula_expression: str = "DETERMINISTIC_FIXED"
    installments_count: Optional[int] = None
    installment_amount: Optional[float] = None
    evidence_id: Optional[str] = None
    raw_source_text: str = ""


class BenefitFormulaEngine:
    """Extracts and evaluates deterministic welfare formulas."""

    def __init__(self):
        pass

    def parse_benefit_summary(
        self,
        candidate_id: str,
        raw_summary: Any,
        evidence_anchor: Optional[EvidenceAnchor] = None,
    ) -> BenefitFormula:
        text = self._flatten_text(raw_summary)
        lower = text.lower()
        evidence_id = evidence_anchor.evidence_id if evidence_anchor else None

        # 1. Emergency service (e.g. 108 Ambulance)
        if "108" in lower or "ambulance" in lower or "emergency service" in lower:
            return BenefitFormula(
                benefit_id=f"ben-{candidate_id}",
                candidate_id=candidate_id,
                benefit_type=BenefitType.SERVICE_EMERGENCY,
                cadence=PaymentCadence.ON_EVENT,
                nominal_amount=0.0,
                benefit_description="Free emergency medical response, ambulance transport, and trauma stabilization 24x7.",
                formula_expression="100_PERCENT_STATE_FUNDED_SERVICE",
                evidence_id=evidence_id,
                raw_source_text=text[:300],
            )

        # 2. Insurance Cover (e.g. PMJJBY / PMSBY / PMJAY)
        m_cover = re.search(r"(?:insurance|life|health|cover|accidental)?\s*(?:of|up to|worth)?\s*(?:rs\.?|₹|inr)?\s*([\d,]+)\s*(?:lakh|lakhs|crore)?", lower)
        if "bima" in lower or "insurance" in lower or "cover" in lower:
            amount = self._extract_amount(text)
            return BenefitFormula(
                benefit_id=f"ben-{candidate_id}",
                candidate_id=candidate_id,
                benefit_type=BenefitType.INSURANCE_COVER,
                cadence=PaymentCadence.ON_EVENT,
                nominal_amount=amount or 200000.0,
                benefit_description=f"Statutory insurance protection coverage: {text[:120]}.",
                formula_expression="POLICY_CLAIM_SETTLEMENT",
                evidence_id=evidence_id,
                raw_source_text=text[:300],
            )

        # 3. PM-KISAN / Regular Cash DBT
        if "6,000" in text or "6000" in text:
            if "installment" in lower or "kisan" in lower or "year" in lower:
                return BenefitFormula(
                    benefit_id=f"ben-{candidate_id}",
                    candidate_id=candidate_id,
                    benefit_type=BenefitType.CASH_TRANSFER,
                    cadence=PaymentCadence.ANNUAL,
                    nominal_amount=6000.0,
                    installments_count=3,
                    installment_amount=2000.0,
                    benefit_description="Direct Benefit Transfer of ₹6,000 per year credited directly to Aadhaar-seeded bank account in three equal installments of ₹2,000.",
                    formula_expression="EQUAL_INSTALLMENTS(6000, 3)",
                    evidence_id=evidence_id,
                    raw_source_text=text[:300],
                )

        # 4. Pension (Monthly)
        if "pension" in lower:
            amount = self._extract_amount(text)
            return BenefitFormula(
                benefit_id=f"ben-{candidate_id}",
                candidate_id=candidate_id,
                benefit_type=BenefitType.CASH_TRANSFER,
                cadence=PaymentCadence.MONTHLY,
                nominal_amount=amount or 1000.0,
                benefit_description=f"Monthly social security pension: {text[:120]}.",
                formula_expression="MONTHLY_DIRECT_DEPOSIT",
                evidence_id=evidence_id,
                raw_source_text=text[:300],
            )

        # 5. Generic Cash / Subsidy extraction
        amount = self._extract_amount(text)
        b_type = BenefitType.CASH_TRANSFER if amount else BenefitType.IN_KIND_SUBSIDY

        return BenefitFormula(
            benefit_id=f"ben-{candidate_id}",
            candidate_id=candidate_id,
            benefit_type=b_type,
            cadence=PaymentCadence.ONE_TIME if not any(w in lower for w in ["month", "year", "annual"]) else PaymentCadence.ANNUAL,
            nominal_amount=amount,
            benefit_description=text[:200] if text else "Statutory welfare entitlement.",
            formula_expression="DETERMINISTIC_FIXED",
            evidence_id=evidence_id,
            raw_source_text=text[:300],
        )

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extracts first valid rupee amount from text, handling Lakhs."""
        # Check for Lakhs
        m_lakh = re.search(r"(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)\s*lakh", text, re.IGNORECASE)
        if m_lakh:
            try:
                return float(m_lakh.group(1)) * 100000.0
            except ValueError:
                pass

        # Check for direct numeric rupee amount
        m_num = re.search(r"(?:rs\.?|₹|inr)\s*([\d,]+)", text, re.IGNORECASE)
        if m_num:
            try:
                clean = m_num.group(1).replace(",", "")
                return float(clean)
            except ValueError:
                pass
        return None

    def _flatten_text(self, raw: Any) -> str:
        if not raw:
            return ""
        if isinstance(raw, str):
            return raw.strip()
        if isinstance(raw, list):
            res = []
            for it in raw:
                if isinstance(it, str):
                    res.append(it.strip())
                elif isinstance(it, dict):
                    res.append(self._flatten_dict(it))
            return " ".join(res).strip()
        if isinstance(raw, dict):
            return self._flatten_dict(raw)
        return str(raw)

    def _flatten_dict(self, d: Dict[str, Any]) -> str:
        texts = []
        if "text" in d and isinstance(d["text"], str):
            texts.append(d["text"].strip())
        if "children" in d and isinstance(d["children"], list):
            for ch in d["children"]:
                if isinstance(ch, dict):
                    texts.append(self._flatten_dict(ch))
                elif isinstance(ch, str):
                    texts.append(ch.strip())
        return " ".join(texts).strip()
