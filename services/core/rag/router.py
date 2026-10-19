from services.core.rag.corpus import CERTIFIED_SCHEMES_OFFICIAL_CORPUS
"""
Intent Router & Prompt Injection Guard
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Classifies user queries into:
1. ELIGIBILITY_CHECK -> Routes to deterministic EligibilityEngine; RAG grounds reasoning.
2. FACTUAL_QA -> Hybrid retrieval across certified schemes.
3. UNVERIFIED_SCHEME_INQUIRY -> Controlled fallback; zero hallucinations.
4. OUT_OF_SCOPE -> Rejection & public scheme redirection.

Also enforces prompt injection sanitization.
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple

# Comprehensive prompt injection detection patterns (English, Hindi, Hinglish, jailbreaks, control tokens)
INJECTION_PATTERNS: List[re.Pattern] = [
    # Instruction override / ignore / disregard (English)
    re.compile(r'(?:ignore|disregard|forget|override|bypass|cancel|drop|neglect)\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|former|system|initial|existing|current)?\s*(?:instructions?|guidelines?|rules?|system|prompts?|constraints?)', re.IGNORECASE),
    re.compile(r'(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+)?(?:guidelines|rules|constraints|instructions|safety|guardrails)', re.IGNORECASE),
    re.compile(r'(?:declare|mark|approve)\s+(?:all\s+)?(?:applicants?|users?|everyone)\s+(?:as\s+)?(?:eligible|unconditionally)', re.IGNORECASE),
    
    # Jailbreak / mode switching (English)
    re.compile(r'(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|simulate|switch\s+to|enter)\s+(?:in\s+)?(?:a\s+)?(?:developer|dan|jailbreak|unrestricted|god|root|admin|unfiltered)(?:\s+mode)?\b', re.IGNORECASE),
    re.compile(r'\bdo\s+anything\s+now\b', re.IGNORECASE),
    re.compile(r'\bjailbreak\b', re.IGNORECASE),
    re.compile(r'\b(?:dan\s+mode|you\s+are\s+dan|act\s+as\s+dan)\b', re.IGNORECASE),
    
    # Secret / system prompt extraction (English)
    re.compile(r'(?:output|reveal|show|print|display|tell\s+me|give\s+me|leak|repeat|dump|write\s+out)\s+(?:your\s+)?(?:system\s+prompt|instructions?|initial\s+prompt|secret\s*(?:key|token|password)?|hidden\s+prompt|internal\s+(?:rules?|instructions?))', re.IGNORECASE),
    re.compile(r'what\s+(?:is|are)\s+(?:your\s+)?(?:system\s+prompt|internal\s+(?:instructions?|rules?)|hidden\s+rules)', re.IGNORECASE),
    
    # Control tokens & delimiters (including closed tags and system overrides)
    re.compile(r'<\|im_start\|>|<\|im_end\|>|<\|user\|>|<\|assistant\|>|<\|system\|>|\[SYSTEM(?:[\s_]+(?:UPDATE|OVERRIDE))?\]|\[/SYSTEM\]|\[ADMIN(?:[\s_]+(?:UPDATE|OVERRIDE))?\]|\[/ADMIN\]|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>', re.IGNORECASE),

    # Hindi & Hinglish instruction override
    re.compile(r'(?:purane|pichle|sabhi|pehle\s+ke|saare)\s+(?:sabhi\s+|saare\s+)?(?:nirdesh|niyam|rules|instructions?)\s*(?:ko\s+)?(?:bhool\s*jao|bhulo|ignore\s*karo|hatao|radd\s*karo)', re.IGNORECASE),
    re.compile(r'(?:पुराने|पिछले|सभी|सारे)\s+(?:सभी\s+|सारे\s+)?(?:निर्देश|नियम)\s*(?:को\s+)?(?:भूल\s*जाओ|भूलों|रद्द\s*करो|अनदेखा\s*करो|हटाओ)', re.IGNORECASE),
    re.compile(r'(?:nirdesh|niyam|rules|instructions?)\s+(?:bhool\s*jao|bhulo|ignore\s*karo|radd\s*karo|hatao)', re.IGNORECASE),
    re.compile(r'(?:निर्देश|नियम)\s+(?:भूल\s*जाओ|रद्द\s*करो|अनदेखा\s*करो|हटाओ)', re.IGNORECASE),

    # Hindi & Hinglish prompt/secret extraction
    re.compile(r'(?:apna|internal|gupt)\s+(?:system\s*prompt|secret|instructions?|gupt\s*code|api\s*key)\s*(?:dikhao|batao|print\s*karo|reveal\s*karo|bhej[oe])', re.IGNORECASE),
    re.compile(r'(?:अपना|आंतरिक)\s+(?:सिस्टम\s*प्रॉम्प्ट|सीक्रेट|गुप्त\s*कोड|निर्देश)\s*(?:दिखाओ|बताओ|लिखो)', re.IGNORECASE),
    re.compile(r'(?:system\s*prompt|secret\s*key|gupt\s*code)\s+(?:dikhao|batao|bataiye|print\s*karo|reveal\s*karo)', re.IGNORECASE),
    re.compile(r'(?:सिस्टम\s*प्रॉम्प्ट|सीक्रेट)\s+(?:दिखाओ|बताओ)', re.IGNORECASE),

    # Hindi & Hinglish jailbreak / developer mode & fake approvals
    re.compile(r'tum\s+(?:ab\s+)?(?:developer|dan|jailbreak|unrestricted)\s+mode\s+(?:me|mein)\s+ho', re.IGNORECASE),
    re.compile(r'तुम\s+(?:अब\s+)?(?:डेवलपर|जेलब्रेक|दान)\s+मोड\s+में\s+हो', re.IGNORECASE),
    re.compile(r'(?:developer|jailbreak)\s+mode\s+(?:chalu|on)\s+karo', re.IGNORECASE),
    re.compile(r'(?:डेवलपर|जेलब्रेक)\s+मोड\s+(?:चालू|ऑन)\s+करो', re.IGNORECASE),
    re.compile(r'(?:sabhi\s+applicants?|sabko|sab)\s+ko\s+eligible\s+(?:declare|mark|ghoshit)\s+karo', re.IGNORECASE),
    re.compile(r'सभी\s+को\s+पात्र\s+घोषित\s+करो', re.IGNORECASE)
]

HTML_COMMENT_REGEX = re.compile(r'<!--[\s\S]*?-->', re.IGNORECASE)
HTML_TAG_REGEX = re.compile(r'<(?:script|style|iframe|object)[\s\S]*?</(?:script|style|iframe|object)>|<[^>]+>', re.IGNORECASE)
ZERO_WIDTH_REGEX = re.compile(r'[\u200B-\u200F\u2060\uFEFF\u00AD\u00A0]')

LEETSPEAK_MAP = str.maketrans({
    '1': 'i', '!': 'i', '|': 'i',
    '0': 'o',
    '3': 'e',
    '4': 'a', '@': 'a',
    '5': 's', '$': 's',
    '7': 't', '+': 't',
    '8': 'b'
})

SPACED_LETTERS_REGEX = re.compile(r'\b([a-zA-Z][._\-\s]){2,}[a-zA-Z]\b')


def deobfuscate(text: str) -> str:
    """
    Normalizes potentially obfuscated prompt injection attempts:
    - Normalizes Unicode NFKD
    - Strips zero-width & invisible characters
    - Strips HTML comments & script tags
    - Collapses single-letter spaced and delimiter-separated words (e.g. i g n o r e -> ignore)
    - Maps leetspeak homoglyphs (e.g. 1gnore -> ignore)
    """
    norm = unicodedata.normalize('NFKD', text)
    norm = ZERO_WIDTH_REGEX.sub('', norm)
    norm = HTML_COMMENT_REGEX.sub(' ', norm)
    norm = HTML_TAG_REGEX.sub(' ', norm)
    norm = SPACED_LETTERS_REGEX.sub(lambda m: re.sub(r'[._\-\s]', '', m.group(0)), norm)
    norm_leet = norm.translate(LEETSPEAK_MAP)
    return norm_leet

# Eligibility inquiry single words (English, Hindi, Hinglish)
ELIGIBILITY_KEYWORDS: Set[str] = {
    "eligible", "eligibility", "qualify", "qualified", "qualifying",
    "patra", "patrata", "yogyata", "yogya", "exclusion", "excluded",
    "exclusions", "qualifications", "criteria"
}

# Eligibility inquiry multi-word phrases
ELIGIBILITY_PHRASES: List[str] = [
    "can i get", "can i apply", "am i eligible", "do i qualify",
    "kya mujhe", "kya main", "patra hu", "apply kar sakta", "apply kar sakti",
    "tax bharta", "income tax", "pensioner", "eligibility check", "am i excluded",
    "can i receive", "will i get", "kya milega", "shamil ho sakta"
]

# Known popular unverified schemes catalogued in India
COMMON_UNVERIFIED_SCHEMES: Dict[str, str] = {
    "fasal bima": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
    "pmfby": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
    "ladli behna": "Ladli Behna Yojana",
    "sukanya": "Sukanya Samriddhi Yojana",
    "surya ghar": "PM Surya Ghar Muft Bijli Yojana",
    "muft bijli": "PM Surya Ghar Muft Bijli Yojana",
    "naps": "National Apprenticeship Promotion Scheme (NAPS)",
    "apprenticeship": "National Apprenticeship Promotion Scheme (NAPS)",
    "pm poshan": "PM Poshan Shakti Nirman",
    "poshan yojana": "PM Poshan Shakti Nirman",
    "standup india": "Stand Up India Scheme",
    "startup india": "Startup India Scheme",
    "kanya sumangala": "Mukhyamantri Kanya Sumangala Yojana"
}

# Out-of-scope non-governmental markers
OUT_OF_SCOPE_MARKERS: Set[str] = {
    "hdfc", "sbi cards", "icici", "axis bank", "bajaj finance", "credit card limit",
    "cricket", "ipl", "bollywood", "recipe", "weather forecast", "bitcoin",
    "stock market", "crypto", "astrology", "horoscope"
}

# Certified citizen scheme IDs
CERTIFIED_CITIZEN_SCHEMES: Set[str] = set(CERTIFIED_SCHEMES_OFFICIAL_CORPUS.keys())


class IntentRouter:
    """
    Analyzes user queries, sanitizes malicious content, and classifies intent.
    """

    @classmethod
    def sanitize_input(cls, query: str) -> Tuple[str, bool]:
        """
        Hardened detection & sanitization for prompt injection attempts:
        - Detects HTML comments (<!-- ... -->) and dangerous HTML tags (<script>, etc.)
        - De-obfuscates zero-width invisible characters, spaced letters, delimiter padding, and leetspeak
        - Detects English, Hindi, and Hinglish prompt injection instructions
        - Multi-pass sanitization: cleans all matching injection tokens
        Returns (sanitized_query, is_injection_detected).
        """
        is_injection = False
        sanitized = query

        # 1. Check for HTML comments
        html_comments = HTML_COMMENT_REGEX.findall(query)
        if html_comments:
            for comment in html_comments:
                comment_probe = deobfuscate(comment)
                for pat in INJECTION_PATTERNS:
                    if pat.search(comment) or pat.search(comment_probe):
                        is_injection = True
                        break
            # Always neutralize HTML comments from queries
            sanitized = HTML_COMMENT_REGEX.sub('[SANITIZED_INSTRUCTION]', sanitized)
            is_injection = True

        # Strip dangerous HTML tags (<script>, <style>, <iframe>, etc.)
        if HTML_TAG_REGEX.search(sanitized):
            sanitized = HTML_TAG_REGEX.sub('[SANITIZED_TAG]', sanitized)
            is_injection = True

        # 2. Check and sanitize standard patterns in current text
        for pattern in INJECTION_PATTERNS:
            if pattern.search(sanitized):
                sanitized = pattern.sub("[SANITIZED_INSTRUCTION]", sanitized)
                is_injection = True

        # 3. Check deobfuscated probe text
        probe = deobfuscate(sanitized)
        for pattern in INJECTION_PATTERNS:
            if pattern.search(probe):
                is_injection = True
                # Replace matching patterns
                sanitized = pattern.sub("[SANITIZED_INSTRUCTION]", sanitized)
                # Remove zero-width characters and collapse spaced/delimited tokens directly
                sanitized = ZERO_WIDTH_REGEX.sub('', sanitized)
                sanitized = SPACED_LETTERS_REGEX.sub(lambda m: re.sub(r'[._\-\s]', '', m.group(0)), sanitized)
                if pattern.search(sanitized):
                    sanitized = pattern.sub("[SANITIZED_INSTRUCTION]", sanitized)
                else:
                    leet_san = sanitized.translate(LEETSPEAK_MAP)
                    if pattern.search(leet_san):
                        sanitized = pattern.sub("[SANITIZED_INSTRUCTION]", leet_san)

        # Clean whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized, is_injection

    @classmethod
    def classify_intent(cls, normalized_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies query intent into ELIGIBILITY_CHECK, FACTUAL_QA,
        UNVERIFIED_SCHEME_INQUIRY, or OUT_OF_SCOPE.
        """
        raw_query = normalized_payload.get("raw_query", "")
        sanitized_query, injection_detected = cls.sanitize_input(raw_query)

        # Check if entire query was an injection payload with no legitimate text left
        clean_text_check = re.sub(r'\[SANITIZED_[A-Z]+\]', '', sanitized_query)
        clean_text_check = re.sub(r'[^\w\s]', '', clean_text_check).strip()
        if injection_detected and not clean_text_check:
            return {
                "intent": "FACTUAL_QA",
                "reason": "Prompt injection detected and neutralized.",
                "sanitized_query": sanitized_query,
                "injection_detected": True,
                "scheme_id": None
            }

        lower_query = sanitized_query.lower()

        # 1. Out-of-scope check (match full words to prevent substring false positives like 'ipl' in 'multiple')
        for oos in OUT_OF_SCOPE_MARKERS:
            if re.search(r'\b' + re.escape(oos) + r'\b', lower_query):
                return {
                    "intent": "OUT_OF_SCOPE",
                    "reason": f"Query references private finance or non-welfare domain: '{oos}'",
                    "sanitized_query": sanitized_query,
                    "injection_detected": injection_detected,
                    "scheme_id": None
                }

        # 2. Check for explicit unverified scheme mention
        for unv_key, unv_title in COMMON_UNVERIFIED_SCHEMES.items():
            # Ensure it's not a substring of a verified scheme
            if unv_key in lower_query:
                # Double check that user is not asking about verified schemes
                candidates = normalized_payload.get("candidate_schemes", [])
                is_verified = any(c[0] in CERTIFIED_CITIZEN_SCHEMES for c in candidates)
                if not is_verified:
                    return {
                        "intent": "UNVERIFIED_SCHEME_INQUIRY",
                        "unverified_scheme_name": unv_title,
                        "reason": f"Scheme '{unv_title}' is currently unverified in CivixAI.",
                        "sanitized_query": sanitized_query,
                        "injection_detected": injection_detected,
                        "scheme_id": None
                    }

        # 3. Check for Institutional Gated Schemes (DDRS, Mission Vatsalya)
        if "ddrs" in lower_query or "deen dayal disabled" in lower_query:
            return {
                "intent": "UNVERIFIED_SCHEME_INQUIRY",
                "unverified_scheme_name": "Deen Dayal Disabled Rehabilitation Scheme (DDRS)",
                "reason": "DDRS is an institutional grant for non-profit organizations/NGOs and is gated from citizen queries.",
                "sanitized_query": sanitized_query,
                "injection_detected": injection_detected,
                "scheme_id": "dbtbharat_central_schemes_deen_dayal_disabled_rehabilitation_scheme"
            }
        if "mission vatsalya" in lower_query or "vatsalya" in lower_query or "child care institution" in lower_query:
            return {
                "intent": "UNVERIFIED_SCHEME_INQUIRY",
                "unverified_scheme_name": "Mission Vatsalya",
                "reason": "Mission Vatsalya is an institutional grant for child protection and child care institutions and is gated from direct citizen queries.",
                "sanitized_query": sanitized_query,
                "injection_detected": injection_detected,
                "scheme_id": "central_mwcd_mission_vatsalya"
            }

        # 4. Check for Eligibility Check vs Factual QA
        words = set(re.findall(r'\b\w+\b', lower_query))
        matching_eligibility = words.intersection(ELIGIBILITY_KEYWORDS)
        
        # Also check phrase matches
        has_eligibility_phrase = any(phrase in lower_query for phrase in ELIGIBILITY_PHRASES)

        candidates = normalized_payload.get("candidate_schemes", [])
        primary_scheme_id = candidates[0][0] if candidates else None

        if matching_eligibility or has_eligibility_phrase:
            return {
                "intent": "ELIGIBILITY_CHECK",
                "reason": "User is inquiring about eligibility qualifications or exclusions.",
                "sanitized_query": sanitized_query,
                "injection_detected": injection_detected,
                "scheme_id": primary_scheme_id
            }

        # 5. Default to FACTUAL_QA
        return {
            "intent": "FACTUAL_QA",
            "reason": "User is seeking factual scheme information, benefits, or procedures.",
            "sanitized_query": sanitized_query,
            "injection_detected": injection_detected,
            "scheme_id": primary_scheme_id
        }
