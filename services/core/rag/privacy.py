"""
CivixAI Query Trace Privacy & PII Scrubbing Engine
Phase 4: Citizen Privacy Protection & Minimal Fact Forwarding

Enforces:
1. PII Masking: Redacts Aadhaar numbers (12-digit patterns), Indian mobile numbers (10-digit with optional +91/0),
   PAN card numbers (5 letters + 4 digits + 1 letter), email addresses, and personal profile facts
   (names, explicit income amounts) from queries, traces, and vector inputs.
2. Configurable Raw Query Storage: Default `store_raw_query: bool = False` prevents raw citizen
   queries containing sensitive personal data from persisting in forensic audit logs.
3. Minimal Fact Forwarding: `filter_minimal_profile_facts(user_facts, target_scheme_rules)` forwards
   ONLY the exact applicant facts referenced by statutory AST rules for deterministic evaluation.
4. Vector Representation Isolation: Ensures citizen profile facts and unmasked PII never enter
   dense vector representations or semantic index search queries.
"""
import re
from typing import Any, Dict, List, Optional, Set, Union


# ── PII Regular Expressions ──────────────────────────────────────────────────

# Aadhaar: 12 digits, spaced (4-4-4), hyphenated (4-4-4), or contiguous 12 digits (not preceded by +)
AADHAAR_REGEX = re.compile(
    r'(?<!\+)(?<!\d)(?:\d{4}[\s-]\d{4}[\s-]\d{4}|\d{12})(?!\d)'
)

# Indian mobile numbers: 10 digits starting with 6, 7, 8, 9 with optional +91/0 prefix and optional space/hyphen
PHONE_REGEX = re.compile(
    r'(?<!\d)(?:(?:\+91|0)[\s-]?)?[6-9]\d{9}(?!\d)|(?<!\d)(?:(?:\+91|0)[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)'
)

# PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
PAN_REGEX = re.compile(
    r'\b[A-Za-z]{5}[0-9]{4}[A-Za-z]\b'
)

# Email address
EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
)

# Personal Names (English, Hinglish, Devanagari Hindi patterns)
NAME_EN_PATTERNS = [
    re.compile(r'\b(?:my\s+name\s+is|name\s+is|myself|i\s+am|applicant\s+name\s+is|applicant\s*:|name\s*:)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b', re.IGNORECASE),
]
NAME_HINGLISH_PATTERNS = [
    re.compile(r'\b(?:mera\s+naam|humara\s+naam|apna\s+naam)\s+([A-Za-z]+(?:\s+[A-Za-z]+){1,3})(?:\s+(?:hai|h|bhi))?\b', re.IGNORECASE),
]
NAME_HINDI_PATTERNS = [
    re.compile(r'\b(?:मेरा\s+नाम|हमारा\s+नाम|नाम\s*:)\s+([\u0900-\u097F]+(?:\s+[\u0900-\u097F]+){1,3})(?:\s+है)?\b'),
]

# Explicit Income Amounts (English, Hinglish, Hindi)
INCOME_PATTERNS = [
    re.compile(
        r'(?i)\b(?:annual|monthly|family|household|total|net)?\s*(?:income|salary|earning|earnings|kamai|aay|कमाई|आय|वेतन)\s*(?:is|hai|of|:|h|around|approx|approximately|pe|se)?\s*(?:rs\.?|inr|₹)?\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakhs?|lac|crore|k|per\s+month|pm|per\s+annum|pa|mahina|salana|varshik|हज़ार|लाख))?'
    ),
    re.compile(
        r'(?i)(?:rs\.?|inr|₹)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakhs?|lac|crore|k))?\s*(?:per\s+month|pm|per\s+annum|pa|salary|income|kamai|aay)'
    )
]


class QueryTracePrivacy:
    """
    Guarantees privacy-first query processing, PII scrubbing, minimal fact forwarding,
    and configurable raw query storage.
    """

    def __init__(self, store_raw_query: bool = False):
        """
        Initializes privacy policy.
        :param store_raw_query: If False (default), raw queries with PII are never persisted in traces.
        """
        self.store_raw_query = store_raw_query

    @classmethod
    def mask_pii(cls, text: str) -> str:
        """
        Comprehensive PII scrubbing:
        - Aadhaar numbers -> [REDACTED_AADHAAR]
        - Indian mobile numbers -> [REDACTED_PHONE]
        - PAN card numbers -> [REDACTED_PAN]
        - Email addresses -> [REDACTED_EMAIL]
        - Personal names -> [REDACTED_NAME]
        - Explicit income amounts -> [REDACTED_INCOME]
        """
        if not text:
            return ""

        masked = text

        # 1. Email addresses (run before name / word replacements)
        masked = EMAIL_REGEX.sub("[REDACTED_EMAIL]", masked)

        # 2. PAN Card numbers (run before Aadhaar/phone to avoid overlap)
        masked = PAN_REGEX.sub("[REDACTED_PAN]", masked)

        # 3. Aadhaar numbers (12-digit patterns)
        masked = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", masked)

        # 4. Indian mobile numbers
        masked = PHONE_REGEX.sub("[REDACTED_PHONE]", masked)

        # 5. Names (English, Hinglish, Devanagari)
        for pat in NAME_EN_PATTERNS:
            def _replace_name_en(match):
                full = match.group(0)
                name = match.group(1)
                return full.replace(name, "[REDACTED_NAME]")
            masked = pat.sub(_replace_name_en, masked)

        for pat in NAME_HINGLISH_PATTERNS:
            def _replace_name_hinglish(match):
                full = match.group(0)
                name = match.group(1)
                return full.replace(name, "[REDACTED_NAME]")
            masked = pat.sub(_replace_name_hinglish, masked)

        for pat in NAME_HINDI_PATTERNS:
            def _replace_name_hindi(match):
                full = match.group(0)
                name = match.group(1)
                return full.replace(name, "[REDACTED_NAME]")
            masked = pat.sub(_replace_name_hindi, masked)

        # 6. Explicit income amounts
        for pat in INCOME_PATTERNS:
            masked = pat.sub("[REDACTED_INCOME]", masked)

        # Clean multiple spaces
        masked = re.sub(r'[ \t]+', ' ', masked).strip()
        return masked

    @classmethod
    def has_pii(cls, text: str) -> bool:
        """
        Checks if text contains any PII pattern.
        """
        if not text:
            return False
        if EMAIL_REGEX.search(text):
            return True
        if PAN_REGEX.search(text):
            return True
        if AADHAAR_REGEX.search(text):
            return True
        if PHONE_REGEX.search(text):
            return True
        for pat in NAME_EN_PATTERNS + NAME_HINGLISH_PATTERNS + NAME_HINDI_PATTERNS:
            if pat.search(text):
                return True
        for pat in INCOME_PATTERNS:
            if pat.search(text):
                return True
        return False

    def prepare_trace_query(self, raw_query: str, store_raw_query: Optional[bool] = None) -> str:
        """
        Prepares query text for forensic trace storage.
        If raw storage is disabled (default), all PII is redacted.
        """
        allow_raw = self.store_raw_query if store_raw_query is None else store_raw_query
        if allow_raw:
            return raw_query
        return self.mask_pii(raw_query)

    @classmethod
    def sanitize_vector_query(cls, query: str) -> str:
        """
        Ensures that user query passed into dense embeddings or vector indexing
        has all PII scrubbed to prevent PII leakage into vector embeddings.
        """
        return cls.mask_pii(query)

    @staticmethod
    def extract_rule_facts(rules: Any) -> Set[str]:
        """
        Recursively extracts all fact keys required by statutory AST rules.
        Supports RuleNode, ConditionNode, AllNode, AnyNode, NotNode,
        dictionaries, database Rule models, or iterables.
        """
        facts: Set[str] = set()
        if not rules:
            return facts

        if isinstance(rules, str):
            facts.add(rules)
            return facts

        if isinstance(rules, (list, tuple, set)):
            for r in rules:
                facts.update(QueryTracePrivacy.extract_rule_facts(r))
            return facts

        if isinstance(rules, dict):
            if "fact" in rules and isinstance(rules["fact"], str):
                facts.add(rules["fact"])
            if "fact_key" in rules and isinstance(rules["fact_key"], str):
                facts.add(rules["fact_key"])
            if "all" in rules:
                facts.update(QueryTracePrivacy.extract_rule_facts(rules["all"]))
            if "any" in rules:
                facts.update(QueryTracePrivacy.extract_rule_facts(rules["any"]))
            if "not" in rules:
                facts.update(QueryTracePrivacy.extract_rule_facts(rules["not"]))
            if "invert" in rules:
                facts.update(QueryTracePrivacy.extract_rule_facts(rules["invert"]))
            if "rules" in rules:
                facts.update(QueryTracePrivacy.extract_rule_facts(rules["rules"]))
            return facts

        # Pydantic models or SQLAlchemy models
        if hasattr(rules, "fact") and getattr(rules, "fact"):
            facts.add(getattr(rules, "fact"))
        if hasattr(rules, "fact_key") and getattr(rules, "fact_key"):
            facts.add(getattr(rules, "fact_key"))
        if hasattr(rules, "all") and getattr(rules, "all"):
            facts.update(QueryTracePrivacy.extract_rule_facts(getattr(rules, "all")))
        if hasattr(rules, "any") and getattr(rules, "any"):
            facts.update(QueryTracePrivacy.extract_rule_facts(getattr(rules, "any")))
        if hasattr(rules, "invert") and getattr(rules, "invert"):
            facts.update(QueryTracePrivacy.extract_rule_facts(getattr(rules, "invert")))
        if hasattr(rules, "rules") and getattr(rules, "rules"):
            facts.update(QueryTracePrivacy.extract_rule_facts(getattr(rules, "rules")))

        return facts

    @classmethod
    def filter_minimal_profile_facts(
        cls,
        user_facts: Optional[Dict[str, Any]],
        target_scheme_rules: Any
    ) -> Dict[str, Any]:
        """
        Minimal fact forwarding:
        Forwards ONLY the exact applicant facts needed to evaluate statutory AST rules
        for the target scheme. Extraneous facts (e.g. sensitive attributes, unrelated
        financial/demographic facts) are excluded.
        """
        if not user_facts:
            return {}

        required_facts = cls.extract_rule_facts(target_scheme_rules)
        if not required_facts:
            return {}

        # Forward strictly the intersection
        minimal = {
            k: v for k, v in user_facts.items()
            if k in required_facts
        }
        return minimal


# Module-level aliases for backwards compatibility and easy importing
redact_query = QueryTracePrivacy.mask_pii
redact_pii = QueryTracePrivacy.mask_pii
QueryRedactor = QueryTracePrivacy
