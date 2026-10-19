"""
Ingestion Extractor
Extracts candidate rules, benefits, and document requirements from parsed source documents.
All output items are tagged machine_extracted and packaged into staging drafts with exact source fragments.
"""
import re
from typing import List, Dict, Any, Optional
from services.core.facts import FACT_CATALOGUE
from .parser import ParsedDocument
from .normalizer import normalize_state, parse_currency_amount, extract_age_bounds

class CandidateExtraction:
    def __init__(
        self,
        proposed_summary: str,
        proposed_description: str,
        rule_drafts: List[Dict[str, Any]],
        benefit_drafts: List[Dict[str, Any]],
        document_drafts: List[Dict[str, Any]],
        source_snapshot_id: Optional[str] = None
    ):
        self.proposed_summary = proposed_summary
        self.proposed_description = proposed_description
        self.rule_drafts = rule_drafts
        self.benefit_drafts = benefit_drafts
        self.document_drafts = document_drafts
        self.source_snapshot_id = source_snapshot_id

class RuleExtractor:
    """
    Deterministic rule and benefit extractor matching against canonical FACT_CATALOGUE.
    """
    @classmethod
    def extract_from_document(
        cls,
        doc: ParsedDocument,
        source_snapshot_id: Optional[str] = None
    ) -> CandidateExtraction:
        rules: List[Dict[str, Any]] = []
        benefits: List[Dict[str, Any]] = []
        documents: List[Dict[str, Any]] = []

        seen_facts = set()

        for sec in doc.sections:
            text = sec.content
            fragment = sec.fragment_id

            # 1. Age Range Extraction
            if "person.age" not in seen_facts:
                age_min, age_max = extract_age_bounds(text)
                if age_min is not None and age_max is not None:
                    rules.append({
                        "fact_key": "person.age",
                        "operator": "between",
                        "expected_value": f"[{age_min}, {age_max}]",
                        "mandatory": True,
                        "scope": "applicant",
                        "reason_code": "AGE_ELIGIBILITY",
                        "source_fragment": fragment[:255]
                    })
                    seen_facts.add("person.age")
                elif age_min is not None:
                    rules.append({
                        "fact_key": "person.age",
                        "operator": "gte",
                        "expected_value": str(age_min),
                        "mandatory": True,
                        "scope": "applicant",
                        "reason_code": "MIN_AGE_CRITERIA",
                        "source_fragment": fragment[:255]
                    })
                    seen_facts.add("person.age")
                elif age_max is not None:
                    rules.append({
                        "fact_key": "person.age",
                        "operator": "lte",
                        "expected_value": str(age_max),
                        "mandatory": True,
                        "scope": "applicant",
                        "reason_code": "MAX_AGE_CEILING",
                        "source_fragment": fragment[:255]
                    })
                    seen_facts.add("person.age")

            # 2. Income Ceiling Extraction
            if "household.annual_income" not in seen_facts:
                income_match = re.search(r"(?:income|annual\s*income|family\s*income)[^\.\n]*(?:not\s*exceeding|below|less\s*than|up\s*to)\s*(?:₹|rs\.?)?\s*([0-9,]+(?:\s*(?:lakh|lac|crore))?)", text, re.IGNORECASE)
                if income_match:
                    amount = parse_currency_amount(income_match.group(1))
                    if amount and amount > 0:
                        rules.append({
                            "fact_key": "household.annual_income",
                            "operator": "lte",
                            "expected_value": str(amount),
                            "mandatory": True,
                            "scope": "household",
                            "reason_code": "INCOME_CEILING",
                            "source_fragment": fragment[:255]
                        })
                        seen_facts.add("household.annual_income")

            # 3. State Domicile Extraction
            if "location.state" not in seen_facts:
                for raw_state in ["Uttar Pradesh", "Bihar", "Maharashtra", "Tamil Nadu", "Karnataka", "Rajasthan", "Madhya Pradesh", "Gujarat", "Delhi"]:
                    if re.search(rf"\b(?:resident\s*of(?:\s*the\s*state\s*of)?|domicile\s*of(?:\s*the\s*state\s*of)?|in\s*the\s*state\s*of|state\s*of)\s+{raw_state}\b", text, re.IGNORECASE):
                        canon_state = normalize_state(raw_state)
                        if canon_state:
                            rules.append({
                                "fact_key": "location.state",
                                "operator": "eq",
                                "expected_value": f'"{canon_state}"',
                                "mandatory": True,
                                "scope": "applicant",
                                "reason_code": "STATE_DOMICILE",
                                "source_fragment": fragment[:255]
                            })
                            seen_facts.add("location.state")
                            break

            # 4. Gender restriction
            if "person.gender" not in seen_facts:
                if re.search(r"\b(?:only\s*for\s*women|female\s*applicants\s*only|girl\s*child|women\s*only)\b", text, re.IGNORECASE):
                    rules.append({
                        "fact_key": "person.gender",
                        "operator": "eq",
                        "expected_value": '"female"',
                        "mandatory": True,
                        "scope": "applicant",
                        "reason_code": "GENDER_RESTRICTION",
                        "source_fragment": fragment[:255]
                    })
                    seen_facts.add("person.gender")

            # 5. Benefits Extraction
            benefit_match = re.search(r"(?:financial\s*assistance|cash\s*transfer|grant|subsidy|incentive)\s*of\s*(?:₹|rs\.?)?\s*([0-9,]+(?:\s*(?:lakh|lac|crore))?)\s*(?:per\s*(?:year|annum|month)|one-time)?", text, re.IGNORECASE)
            if benefit_match and not benefits:
                amt = parse_currency_amount(benefit_match.group(1))
                freq = "yearly" if "year" in text.lower() or "annum" in text.lower() else ("monthly" if "month" in text.lower() else "one_time")
                if amt:
                    benefits.append({
                        "benefit_type": "cash_transfer",
                        "amount_type": "fixed",
                        "fixed_amount": amt,
                        "frequency": freq,
                        "description": benefit_match.group(0).strip()[:200],
                        "source_fragment": fragment[:255]
                    })

            # 6. Document Requirements Extraction
            doc_patterns = [
                ("Aadhaar Card", r"\b(?:aadhaar|adhar|uidai)\b"),
                ("Income Certificate", r"\b(?:income\s*certificate|income\s*proof)\b"),
                ("Domicile Certificate", r"\b(?:domicile|residence\s*certificate|prc)\b"),
                ("Caste Certificate", r"\b(?:caste\s*certificate|category\s*certificate)\b"),
                ("Bank Passbook", r"\b(?:bank\s*passbook|bank\s*account\s*details|cancelled\s*cheque)\b"),
                ("Land Records / RoR", r"\b(?:land\s*records|khatoni|khasra|patta|ror)\b")
            ]
            for doc_name, pat in doc_patterns:
                if re.search(pat, text, re.IGNORECASE):
                    if not any(d["document_type"] == doc_name for d in documents):
                        documents.append({
                            "document_type": doc_name,
                            "is_mandatory": True,
                            "source_fragment": fragment[:255]
                        })

        summary = doc.title
        desc = doc.full_text[:500] if len(doc.full_text) > 500 else doc.full_text

        return CandidateExtraction(
            proposed_summary=summary,
            proposed_description=desc,
            rule_drafts=rules,
            benefit_drafts=benefits,
            document_drafts=documents,
            source_snapshot_id=source_snapshot_id
        )
