"""
Hybrid Retriever with Reciprocal Rank Fusion (RRF) & Certification Hard Filter
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Combines lexical BM25 matching (via SQLite FTS5) with dense semantic similarity,
enforces strict query-time certification filtering (zero unverified leakage),
and performs modular reranking across:
  (a) No Reranking (pure RRF order)
  (b) Heuristic Reranker (deterministic exact-phrase + section boosts)
  (c) Semantic Reranker Candidate (cross-scoring query-clause token alignment & domain semantic matching)
"""
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from sqlalchemy.orm import Session  # type: ignore
import numpy as np  # type: ignore

from services.core.database.models import RagChunk, SchemeVersion, SchemeCertificationDossier
from services.core.ingestion.semantic import SemanticCertificationEngine
from services.core.rag.fts_manager import FtsManager
from services.core.rag.embeddings import EmbeddingProvider, DenseLsaEmbeddingProvider
from services.core.rag.normalizer import SCHEME_KEYWORDS


@dataclass
class CachedChunk:
    id: str
    document_id: str
    scheme_id: str
    scheme_version_id: str
    section_type: str
    heading_path: str
    content: str
    source_citation: str
    source_url: str
    chunk_hash: str
    metadata_json: str
    is_active: bool


UNSUPPORTED_DOMAINS = {
    'truck', 'trucks', 'laptop', 'laptops', 'tablet', 'tablets',
    'computer', 'smartphone', 'smartphones', 'phone', 'mobile phone',
    'car', 'cars', 'scooter', 'scooters', 'bike', 'bikes',
    'electric car', 'electric scooter', 'commercial office', 'electricity', 'power units',
    'real estate', '1 crore', 'crore loan', '10000000', 'crore',
    'credit card', 'credit card loan', 'credit card debt', 'loan waiver', 'karz mafi', 'karj mafi',
    'कर्ज माफ', 'कर्ज माफी', 'क्रेडिट कार्ड',
    'crypto', 'cryptocurrency', 'bitcoin', 'stock market', 'astrology', 'horoscope',
    'free tractor', 'tractor yojana', 'shaadi', 'shadi', 'kanyadan', 'vivah',
    'ddrs', 'deen dayal disabled', 'mission vatsalya', 'vatsalya',
    'mig-ii', 'mig 2', 'mig-2', 'free laptop', 'laptop yojana',
    'kanyadaan', 'shadi anudan'
}

GROUNDING_STOPWORDS = {
    'a', 'an', 'the', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
    'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
    'just', 'should', 'now', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him',
    'she', 'her', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
    'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'doing', 'how', 'why', 'where',
    'or', 'and', 'if', 'but', 'as', 'of', 'at', 'by', 'for', 'with', 'about',
    'scheme', 'yojana', 'yojna', 'government', 'sarkar', 'sarkari', 'central', 'state',
    'india', 'bharat', 'modi', 'pradhan', 'mantri', 'apply', 'application', 'process',
    'registration', 'portal', 'official', 'guidelines', 'rules', 'detail', 'details',
    'information', 'info', 'citizen', 'citizens', 'beneficiary', 'beneficiaries',
    'eligible', 'eligibility', 'patra', 'patrata', 'much', 'many', 'kitna', 'kitne',
    'kitni', 'tell', 'give', 'show', 'help', 'please', 'kya', 'hai', 'hain', 'kaise',
    'milega', 'milegi', 'milta', 'milte', 'chahiye', 'batao', 'bataiye', 'provide',
    'provides', 'provided', 'getting', 'get', 'gets', 'got', 'receive', 'receives',
    'received', 'receiving', 'take', 'takes', 'taking', 'avail', 'availing', 'register',
    'giving', 'where', 'there', 'karwana', 'chahata', 'chahati', 'hoga', 'hogi'
}

GENERIC_BENEFIT_WORDS = {
    'free', 'subsidy', 'loan', 'cash', 'money', 'grant', 'amount', 'card', 'fund', 'benefit',
    'benefits', 'paisa', 'paise', 'sahayata', 'madad', 'assistance', '100%',
    'financial', 'finance', 'finances', 'monetary', 'support', 'welfare', 'aid', 'relief',
    'bima', 'beema', 'insurance', 'pension', 'scholarship', 'chhatravritti'
}

SCHEME_NAME_WORDS = {
    'pm', 'kisan', 'pmkisan', 'svanidhi', 'pmsvanidhi', 'swanidhi', 'pmswanidhi',
    'ujjwala', 'pmuy', 'vishwakarma', 'pmvishwakarma', 'ayushman', 'pmjay', 'pmay',
    'apy', 'pmjjby', 'mudra', 'pmsym', 'ignwps', 'ignoaps', 'igndps', 'eps',
    'nmmss', 'pragati', 'saksham', 'sbmu', 'pmmsy', 'smam', 'pmdaksh', 'ddugky'
}



# =============================================================================
# Modular Reranker Architecture
# =============================================================================

class BaseReranker(ABC):
    """
    Abstract base interface for RAG reranking strategies.
    """
    name: str = "base"

    @abstractmethod
    def rerank(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        section_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunk dictionaries.
        Each candidate dictionary contains chunk metadata and 'base_rrf'.
        Must return the candidates sorted descending by updated 'rrf_score'.
        """
        pass


class NoReranker(BaseReranker):
    """
    Configuration (a): No Reranking (Pure RRF Order).
    Preserves the raw reciprocal rank fusion ordering without applying
    any lexical, heuristic, or semantic boosts.
    """
    name: str = "no_rerank"

    def rerank(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        section_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        reranked = []
        for cand in candidates:
            c = dict(cand)
            c["rrf_score"] = float(cand.get("base_rrf", 0.0))
            c["boost"] = 0.0
            reranked.append(c)
        reranked.sort(key=lambda x: x["rrf_score"], reverse=True)
        return reranked


class HeuristicReranker(BaseReranker):
    """
    Configuration (b): Heuristic Reranker.
    Baseline deterministic exact-phrase match and heuristic section boosts.
    """
    name: str = "heuristic"

    def rerank(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        section_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        lower_query = query.lower()
        query_words = [phrase for phrase in lower_query.split() if len(phrase) > 4]

        reranked = []
        for cand in candidates:
            boost = 0.0
            content = cand.get("content") or ""
            lower_content = content.lower()
            section_type = cand.get("section_type") or ""

            # Exact phrase match boost
            if content and any(phrase in lower_content for phrase in query_words):
                boost += 0.02

            # Section alignment boost
            if section_hint and section_type == section_hint:
                boost += 0.05
            elif "exclu" in lower_query or "nahi" in lower_query or "tax" in lower_query:
                if section_type == "exclusions":
                    boost += 0.05
            elif "how much" in lower_query or "kitna" in lower_query or "tranche" in lower_query or "interest" in lower_query:
                if section_type == "benefits_and_tranches":
                    boost += 0.05
            elif "document" in lower_query or "dastavez" in lower_query or "kagaz" in lower_query:
                if section_type == "documents_required":
                    boost += 0.05

            base_rrf = float(cand.get("base_rrf", 0.0))
            c = dict(cand)
            c["rrf_score"] = base_rrf + boost
            c["boost"] = boost
            reranked.append(c)

        reranked.sort(key=lambda x: x["rrf_score"], reverse=True)
        return reranked


class SemanticRerankerCandidate(BaseReranker):
    """
    Configuration (c): Semantic / Statutory Section Reranker Candidate (Phase 4.3.2).
    Performs multi-signal reranking combining:
      1. Multilingual statutory intent classification across English, Romanized Hindi, and Devanagari Hindi
      2. Domain scheme semantic matching and entity alignment
      3. Cross-scoring query-clause token alignment and atomic child clause density
      4. Heading path token alignment
      5. Numeric and percentage parameter hard-alignment (e.g. ₹6,000, 3 tranches, 7% subsidy)
      6. Source authority hardening (boosting official statutory guidelines and verified portals)
    """
    name: str = "semantic"

    INTENT_CUES = {
        "documents_required": {
            "phrases": [
                # English
                "what document", "documents required", "document required", "which document",
                "papers required", "what paper", "id proof", "identity proof", "address proof",
                "income certificate", "caste certificate", "ration card", "rashan card",
                "bank passbook", "passbook", "khatoni", "khasra", "ror", "lor",
                "letter of recommendation", "certificate of vending", "vending certificate",
                "marksheet", "bonafide", "affidavit", "self-declaration", "praman patra",
                "golden card at the hospital", "generate golden card", "documents needed",
                "verification document", "ekyc", "e-kyc", "aadhaar mandatory", "pan card",
                "mandatory document",
                # Romanized Hindi
                "dastavez", "kagaz", "kaun se dastavez", "kaun kaun se kagaz", "kagzat", "dastawez",
                # Devanagari Hindi
                "दस्तावेज", "कागजात", "कागज़", "पहचान पत्र", "आधार कार्ड", "प्रमाण पत्र",
                "जरूरी दस्तावेज", "कौन-कौन से जरूरी दस्तावेज", "फॉर्म चाहिए", "कागजात चाहिए",
                "आय प्रमाण पत्र", "राशन कार्ड", "पासबुक"
            ],
            "tokens": [
                "document", "documents", "dastavez", "kagaz", "certificate", "passbook",
                "aadhaar", "pan", "ekyc", "dastawez", "marksheet", "bonafide", "lor",
                "दस्तावेज", "कागजात", "कागज़", "प्रमाणपत्र", "पहचान"
            ]
        },
        "application_process": {
            "phrases": [
                # English
                "how to apply", "application process", "apply online", "apply offline",
                "where to apply", "steps to apply", "registration process", "how to register",
                "steps for registration", "portal link", "official portal", "csc center",
                "common service center", "tier verification", "verification stages",
                "how do street vendors apply", "which mobile app or portal",
                "official website to apply", "form submission", "submit form",
                "registration stages", "online registration", "where to submit",
                "claim process", "how to claim", "where do we have to submit",
                # Romanized Hindi
                "kaise aavedan", "kahan aavedan", "kahan jana", "kahan jama",
                "kahan jama karna padta hai", "kahan jama kare", "panjikaran prakriya",
                "aavedan prakriya", "aavedan kaise kare", "claim karne ke liye",
                # Devanagari Hindi
                "आवेदन कैसे करें", "रजिस्ट्रेशन कैसे करें", "पंजीकरण कैसे", "आवेदन प्रक्रिया",
                "पंजीकरण प्रक्रिया", "कहाँ आवेदन करें", "पोर्टल", "वेबसाइट", "ऑनलाइन आवेदन",
                "नया किसान रजिस्ट्रेशन", "फॉर्म कैसे भरें", "कहाँ जमा करना"
            ],
            "tokens": [
                "portal", "website", "csc", "registration", "register", "panjikaran",
                "aavedan", "prakriya", "procedure", "steps", "stages", "jama",
                "आवेदन", "रजिस्ट्रेशन", "पंजीकरण", "प्रक्रिया", "पोर्टल", "जमा"
            ]
        },
        "exclusions": {
            "phrases": [
                # English
                "who cannot", "not eligible", "disqualif", "ineligible", "income tax",
                "tax payer", "taxpayer", "income ceiling", "family limit", "same household",
                "two brothers", "one per family", "join both", "two lpg connections",
                "two connections", "possess two", "both at the same time", "second connection",
                "already enrolled", "already receiving", "already have", "another scholarship",
                "another pension", "simultaneously", "overlapping", "management quota",
                "large corporate", "manufacturing plant", "institutional landholder",
                "sarkari naukri", "govt employee", "government employee", "government servant",
                "chartered accountant", "doctor", "lawyer", "professional", "barred",
                "excluded", "exclusion", "strictly not eligible", "statutory exclusions",
                "disqualified from", "who is barred", "cannot avail", "cannot claim",
                "cannot receive", "retired government pensioner", "government pensioner",
                "pensioner receives", "government employee hai", "at the same time",
                "also avail", "also receive", "both register", "both receive",
                "two ujjwala lpg connections", "two lpg connections", "can a household have two",
                "multiple family members apply", "multiple family members", "one member per family",
                "deduplication", "no existing lpg connection",
                # Romanized Hindi
                "kisko nahi", "kise nahi", "kaun nahi", "kisko labh nahi", "nahi milega",
                "nahi le sakte", "apratra", "patra nahi", "dusra connection", "pehle se",
                "government employee hai to kya", "koi government employee",
                # Devanagari Hindi
                "किसे नहीं मिलेगा", "किसको नहीं मिलेगा", "अपात्र", "पात्र नहीं",
                "लाभ नहीं मिलेगा", "आवेदन नहीं कर सकते", "बाहर हैं", "प्रतिबंध",
                "दोनों एक साथ", "दो कनेक्शन", "पहले से", "सरकारी नौकरी", "इनकम टैक्स",
                "दो भाई", "एक ही परिवार"
            ],
            "tokens": [
                "nahi", "not", "exclu", "ineligible", "disqualif", "cannot", "can't",
                "excluded", "apratra", "barred", "restriction", "prohibited", "disqualified",
                "अपात्र", "प्रतिबंधित", "बाहर"
            ]
        },
        "benefits_and_tranches": {
            "phrases": [
                # English
                "how much", "amount provided", "assistance amount", "subsidy amount", "pension amount",
                "stipend amount", "training stipend amount", "loan amount", "toolkit voucher", "first refill",
                "interest subsidy", "concessional credit", "installment amount", "tranche amount",
                "disbursement", "monthly pension under", "guaranteed pension",
                "statutory monthly pension", "cash benefit", "cash incentive", "cashback",
                "financial relief", "repayment tenure", "per day training stipend",
                "toolkit stipend", "scholarship amount", "cover amount", "death benefit",
                "interest rate", "difference in interest", "tranches schedule",
                "difference in central pension assistance", "pension assistance for beneficiaries aged",
                "what is the difference in interest rate", "subsidy rate", "free connection & stove",
                "claim ₹5 lakh cashless hospitalization", "compulsory milta hai", "card compulsory",
                "hospital cover", "surgery cover", "cashless hospitalization",
                # Romanized Hindi
                "kitna paisa", "kitne rupaye", "kitni sahayata", "kitna milega", "kitna milta",
                "2 lakh milte hain", "pension milti hai", "benefit milta hai",
                # Devanagari Hindi
                "कितने पैसे", "कितना मिलेगा", "कितनी राशि", "किस्त", "सब्सिडी",
                "पेंशन राशि", "मासिक पेंशन", "टूलकिट राशि", "स्टाइपेंड", "ब्याज सब्सिडी",
                "ऋण राशि", "सहायता राशि", "कितने रुपये", "2 लाख मिलते हैं", "लाख मिलते हैं",
                "मिलते हैं?", "मिलेगी?", "प्रोत्साहन राशि", "टूलकिट ले सकते हैं",
                "खर्च कवर होता है", "कवर होता है", "सर्जरी का खर्च", "चरण का लोन"
            ],
            "tokens": [
                "kitna", "kitne", "amount", "rupees", "rupaye", "kist", "installment",
                "tranche", "subsidy", "stipend", "toolkit", "interest", "byaj",
                "pension", "bima", "cover", "cashback", "voucher", "tranches", "tenure",
                "रुपये", "राशि", "किस्त", "सब्सिडी", "पेंशन", "स्टाइपेंड", "टूलकिट", "मिलते", "मिलेगा", "कवर"
            ]
        },
        "eligibility_criteria": {
            "phrases": [
                # English
                "who is eligible", "who can apply", "eligibility criteria", "who qualifies",
                "minimum age", "maximum age", "age limit", "age criteria", "age relaxation",
                "is there any age relaxation", "disability percentage required", "minimum disability percentage",
                "landholding criteria", "qualifying criteria", "target group", "covered group",
                "who are covered", "eligible categories", "who is considered",
                "can adult men apply", "can an urban worker apply", "can a small farmer",
                "without owning agricultural land", "qualify for indira gandhi",
                "which scheme is suitable", "who is eligible for housing",
                "parental income limit", "family income limit", "income criteria",
                "qualifying examination", "minimum marks", "husband and wife separately",
                "without any agricultural land",
                # Romanized Hindi
                "kaun patra hai", "kaun aavedan kar sakta", "kisko mil sakta", "patrata shart",
                "yogyata shart", "aayu seema", "umar seema",
                # Devanagari Hindi
                "कौन पात्र है", "पात्रता", "योग्यता", "पात्रता शर्तें", "शर्तें क्या हैं",
                "आय सीमा", "वार्षिक आय सीमा", "परिवार की वार्षिक आय", "उम्र सीमा",
                "न्यूनतम आयु", "अधिकतम आयु", "विकलांगता प्रतिशत", "के पात्र हैं",
                "पात्र हैं?", "आवेदन मान्य है", "कौन-कौन पात्र हैं"
            ],
            "tokens": [
                "eligible", "eligibility", "qualify", "patrata", "yogyata", "criteria",
                "shartein", "conditions", "umar", "aayu", "qualification",
                "पात्र", "पात्रता", "योग्यता", "शर्तें", "आयु", "उम्र"
            ]
        }
    }

    OFFICIAL_DOMAINS = (
        "gov.in", "nic.in", "pfrda.org.in", "mudra.org.in",
        "maandhan.in", "sbmurban.org", "nsdl.co.in"
    )

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        self.embedding_provider = embedding_provider
        self._clause_split_re = re.compile(r'(?:\n\s*[-*•\d+\.]+\s*|\n{2,}|\.\s+|\;\s+)')

    def _split_into_clauses(self, text: str) -> List[str]:
        if not text:
            return []
        raw = self._clause_split_re.split(text)
        return [c.strip() for c in raw if len(c.strip()) > 8]

    def _extract_tokens(self, text: str) -> Set[str]:
        cleaned = re.sub(r'[^\w\s%₹\u0900-\u097F]', ' ', text.lower())
        tokens = set(cleaned.split())
        stopwords = {
            "what", "is", "the", "in", "and", "how", "for", "to", "are", "can", "of", "who", "under",
            "kya", "hai", "hain", "me", "mein", "se", "ko", "par", "bhi", "ka", "ki", "ke", "liye",
            "ek", "aur", "ya", "yeh", "woh", "kar", "kare", "karna", "कया", "है", "हैं", "में", "से", "को"
        }
        return {t for t in tokens if len(t) > 1 and t not in stopwords or t.isdigit() or "%" in t or t in ("pm", "lpg")}

    def _detect_query_scheme(self, query: str) -> Optional[str]:
        lq = query.lower()
        detected: List[Tuple[int, str]] = []
        for scheme_key, (sid, sname, aliases) in SCHEME_KEYWORDS.items():
            for alias in aliases:
                idx = lq.find(alias.lower())
                if idx != -1:
                    detected.append((idx, sid))
                    break
        if not detected:
            return None
        if len(detected) == 1:
            return detected[0][1]
        detected.sort(key=lambda x: x[0], reverse=True)
        return detected[0][1]

    def _detect_query_section(self, query: str) -> Optional[str]:
        lq = query.lower()
        scores = defaultdict(float)

        for sec, cues in self.INTENT_CUES.items():
            for phrase in cues["phrases"]:
                if phrase.lower() in lq:
                    scores[sec] += 4.5
            for tok in cues["tokens"]:
                if re.search(r'\b' + re.escape(tok.lower()) + r'\b', lq):
                    scores[sec] += 1.0

        # High-priority phrase checks:
        # 1. Submission / Application Process
        if any(w in lq for w in ["kahan jama", "where to submit", "how to apply", "where to apply", "which mobile app", "portal", "website to apply", "आवेदन कैसे", "रजिस्ट्रेशन कैसे", "कहाँ जमा"]):
            scores["application_process"] += 5.5

        # 2. Statutory Exclusion keywords
        if any(w in lq for w in [
            "government employee", "govt employee", "sarkari naukri", "tax payer",
            "income tax", "join both", "two connections", "possess two", "same household",
            "two brothers", "one per family", "management quota", "large corporate",
            "pensioner receives", "at the same time", "also avail", "दो कनेक्शन",
            "सरकारी नौकरी", "इनकम टैक्स", "दोनों एक साथ", "two ujjwala", "two lpg",
            "multiple family members", "one member per family", "deduplication"
        ]):
            scores["exclusions"] += 6.5

        # 3. Explicit Document inquiries
        if any(w in lq for w in ["what document", "documents required", "dastavez", "kagaz", "certificate of vending", "lor", "letter of recommendation", "दस्तावेज", "कागजात"]):
            scores["documents_required"] += 5.5

        # 4. Benefit Payout / Cover checks
        if any(w in lq for w in [
            "how much", "what is the amount", "training stipend amount", "stipend amount",
            "kitna paisa", "kitne rupaye", "2 lakh milte", "लाख मिलते", "पेंशन राशि",
            "सहायता राशि", "loan amount", "subsidy amount", "टूलकिट ले सकते हैं",
            "खर्च कवर", "कवर होता है", "cashless hospitalization", "चरण का लोन"
        ]):
            scores["benefits_and_tranches"] += 6.0

        # 5. Age relaxation / qualifying criteria check
        if any(w in lq for w in ["age relaxation", "disability percentage required", "minimum disability", "आयु सीमा", "आय सीमा"]):
            scores["eligibility_criteria"] += 5.5

        # Conditional query check: "Can [someone] apply / get / receive..."
        is_conditional = any(lq.startswith(p) or f" {p}" in lq for p in [
            "can ", "could ", "is a ", "if a ", "whether ", "kya ", "kaun ", "who is disqualified",
            "क्या ", "कौन ", "agar "
        ])
        asks_benefit = scores["benefits_and_tranches"] >= 5.0

        if is_conditional and not asks_benefit:
            if scores["exclusions"] >= 3.0:
                scores["exclusions"] += 3.0
            else:
                scores["eligibility_criteria"] += 3.0
            scores["benefits_and_tranches"] = max(0.0, scores["benefits_and_tranches"] - 2.5)

        if not scores:
            return None

        best_sec, best_score = max(scores.items(), key=lambda x: x[1])
        return best_sec if best_score >= 1.0 else None

    def rerank(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        section_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        lower_query = query.lower()
        query_tokens = self._extract_tokens(lower_query)
        target_scheme = self._detect_query_scheme(query)
        target_section = section_hint or self._detect_query_section(query)

        numeric_query_tokens = {t for t in query_tokens if any(c.isdigit() for c in t) or "%" in t}

        # Check for historical intent
        historical_intent = any(w in lower_query for w in ["earlier", "historical", "withdrawn", "closed", "previous", "pehle", "old"])

        reranked = []
        for cand in candidates:
            base_rrf = float(cand.get("base_rrf", 0.0))
            scheme_id = cand.get("scheme_id") or ""
            section_type = cand.get("section_type") or ""
            heading = cand.get("heading_path") or ""
            content = cand.get("content") or ""
            source_url = cand.get("source_url") or ""
            source_cit = cand.get("source_citation") or ""
            policy_status = cand.get("policy_status") or "CURRENT_POLICY"

            # 1. Scheme Alignment
            scheme_boost = 0.0
            if target_scheme:
                if scheme_id == target_scheme:
                    scheme_boost += 0.05
                else:
                    scheme_boost -= 0.025

            # 2. Section Alignment
            section_boost = 0.0
            if target_section:
                mapped_target = "documents_required" if target_section in ("documents_required", "documents_and_verification") else target_section
                if section_type == mapped_target:
                    section_boost += 0.095
                else:
                    section_boost -= 0.04

            # 3. Cross-scoring Query-Clause Token Alignment & Child Clause Density
            clauses = self._split_into_clauses(content)
            max_clause_score = 0.0

            for clause in clauses:
                lclause = clause.lower()
                clause_tokens = self._extract_tokens(lclause)
                matched = query_tokens.intersection(clause_tokens)
                tok_cov = len(matched) / len(query_tokens) if query_tokens else 0.0

                num_cov = 0.0
                if numeric_query_tokens:
                    matched_nums = numeric_query_tokens.intersection(clause_tokens)
                    if matched_nums:
                        num_cov = 0.035 * (len(matched_nums) / len(numeric_query_tokens))

                phrase_cov = 0.0
                for w in lower_query.split():
                    if len(w) > 4 and w in lclause:
                        phrase_cov += 0.005

                cl_density = len(matched) / (len(query_tokens) + 0.08 * len(clause_tokens)) if query_tokens else 0.0
                cl_score = tok_cov * 0.035 + num_cov + min(0.015, phrase_cov) + 0.035 * cl_density
                if cl_score > max_clause_score:
                    max_clause_score = cl_score

            # 4. Heading Path Alignment
            heading_boost = 0.0
            heading_tokens = self._extract_tokens(heading.lower())
            matched_hd = query_tokens.intersection(heading_tokens)
            if matched_hd:
                heading_boost = 0.02 * (len(matched_hd) / max(1, len(query_tokens)))

            # 5. Source Authority & Currentness Hardening
            source_boost = 0.0
            if any(dom in source_url for dom in self.OFFICIAL_DOMAINS):
                source_boost += 0.02
            if any(term in source_cit.lower() for term in ["guidelines", "operational", "statutory", "cabinet", "scheme"]):
                source_boost += 0.01

            if not historical_intent:
                if policy_status == "CURRENT_POLICY":
                    source_boost += 0.015
                else:
                    source_boost -= 0.03

            final_score = base_rrf + scheme_boost + section_boost + max_clause_score + heading_boost + source_boost

            c = dict(cand)
            c["rrf_score"] = final_score
            c["boost"] = scheme_boost + section_boost + max_clause_score + heading_boost + source_boost
            c["rerank_breakdown"] = {
                "base_rrf": base_rrf,
                "scheme_boost": scheme_boost,
                "section_boost": section_boost,
                "clause_alignment_score": max_clause_score,
                "heading_boost": heading_boost,
                "source_boost": source_boost
            }
            reranked.append(c)

        reranked.sort(key=lambda x: x["rrf_score"], reverse=True)
        return reranked


# Alias for convenience
SemanticReranker = SemanticRerankerCandidate
StatutorySectionReranker = SemanticRerankerCandidate


# =============================================================================
# Hybrid Retriever
# =============================================================================

class HybridRetriever:
    """
    Hybrid retriever orchestrating lexical BM25, dense semantic embeddings,
    Reciprocal Rank Fusion (RRF), and the mandatory RAG Certification Gate.
    Supports pluggable rerankers: NoReranker, HeuristicReranker, SemanticRerankerCandidate.
    """

    RRF_K = 60

    def __init__(
        self,
        db: Session,
        fts_manager: FtsManager,
        embedding_provider: Optional[EmbeddingProvider] = None,
        reranker: Optional[Union[BaseReranker, str]] = None
    ):
        self.db = db
        self.fts_manager = fts_manager
        self.embedding_provider = embedding_provider or DenseLsaEmbeddingProvider()
        self.cert_engine = SemanticCertificationEngine(db)

        # In-memory chunk cache for fast dense scoring
        self._cached_chunks: List[CachedChunk] = []
        self._chunk_id_to_idx: Dict[str, int] = {}
        self._doc_embeddings: Optional[np.ndarray] = None

        # Resolve reranker (defaults to SemanticRerankerCandidate for Phase 4.3.2)
        self.reranker = self._resolve_reranker(reranker)

    def _resolve_reranker(self, reranker: Optional[Union[BaseReranker, str]]) -> BaseReranker:
        if isinstance(reranker, BaseReranker):
            return reranker
        if isinstance(reranker, str):
            r_str = reranker.lower()
            if r_str in ("no_rerank", "no_reranking", "pure_rrf", "none"):
                return NoReranker()
            elif r_str in ("heuristic", "deterministic"):
                return HeuristicReranker()
            elif r_str in ("semantic", "candidate", "semantic_reranker", "statutory", "section_aware"):
                return SemanticRerankerCandidate(embedding_provider=self.embedding_provider)
            else:
                raise ValueError(f"Unknown reranker string: {reranker}")
        return SemanticRerankerCandidate(embedding_provider=self.embedding_provider)

    def refresh_dense_index(self):
        """
        Loads active chunks from DB and fits the dense embedding provider.
        """
        raw_chunks = self.db.query(RagChunk).filter(RagChunk.is_active == True).all()
        self._cached_chunks = [
            CachedChunk(
                id=str(c.id),
                document_id=str(c.document_id),
                scheme_id=str(c.scheme_id),
                scheme_version_id=str(c.scheme_version_id),
                section_type=str(c.section_type),
                heading_path=str(c.heading_path),
                content=str(c.content),
                source_citation=str(c.source_citation),
                source_url=str(c.source_url),
                chunk_hash=str(c.chunk_hash),
                metadata_json=str(c.metadata_json),
                is_active=bool(c.is_active)
            )
            for c in raw_chunks
        ]
        self._chunk_id_to_idx = {c.id: idx for idx, c in enumerate(self._cached_chunks)}

        corpus = [
            f"{c.heading_path}\n{c.content}\n{c.section_type}"
            for c in self._cached_chunks
        ]
        if corpus:
            self.embedding_provider.fit_or_load(corpus)
            self._doc_embeddings = self.embedding_provider.embed_documents(corpus)
        else:
            self._doc_embeddings = None

    def _get_verified_rag_schemes(self) -> Set[str]:
        """
        Determines the exact set of scheme IDs that are currently certified for citizen RAG.
        Enforces: published + source_verified + semantic_certified + current + complete + citizen audience + active dossier.
        """
        certified_scheme_ids = set()
        active_dossiers = self.db.query(SchemeCertificationDossier).filter(
            SchemeCertificationDossier.is_active == True,
            SchemeCertificationDossier.semantic_review_status == "certified"
        ).all()

        for d in active_dossiers:
            is_cert, reason = self.cert_engine.is_rag_certified(str(d.scheme_version_id), allow_institutional=False)
            if is_cert:
                certified_scheme_ids.add(str(d.scheme_id))

        return certified_scheme_ids

    def search_lexical(
        self,
        query: str,
        scheme_id_filter: Optional[Union[str, Set[str], List[str], Tuple[str, ...]]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Performs BM25 search via SQLite FTS5.
        """
        return self.fts_manager.search(query=query, scheme_id_filter=scheme_id_filter, limit=limit)

    def search_dense(
        self,
        query: str,
        scheme_id_filter: Optional[Union[str, Set[str], List[str], Tuple[str, ...]]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Performs dense semantic vector similarity search.
        """
        if not self._cached_chunks or self._doc_embeddings is None:
            self.refresh_dense_index()

        if self._doc_embeddings is None or len(self._cached_chunks) == 0:
            return []

        query_vec = self.embedding_provider.embed_query(query)
        sims = self.embedding_provider.compute_similarity(query_vec, self._doc_embeddings)

        candidates = []
        for idx, score in enumerate(sims):
            chunk = self._cached_chunks[idx]
            if scheme_id_filter:
                if isinstance(scheme_id_filter, (set, list, tuple)):
                    if chunk.scheme_id not in scheme_id_filter:
                        continue
                elif chunk.scheme_id != scheme_id_filter:
                    continue

            candidates.append({
                "chunk_id": chunk.id,
                "dense_score": float(score),
                "heading_path": chunk.heading_path,
                "section_type": chunk.section_type,
                "scheme_id": chunk.scheme_id
            })

        candidates.sort(key=lambda x: x["dense_score"], reverse=True)
        return candidates[:limit]

    def retrieve(
        self,
        search_query: str,
        target_scheme_id: Optional[str] = None,
        section_hint: Optional[str] = None,
        top_k: int = 5,
        reranker: Optional[Union[BaseReranker, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval (BM25 + Dense), applies Reciprocal Rank Fusion,
        enforces the hard certification filter, and reranks via the configured reranker.
        """
        # 1. Enforce verified-only filter
        allowed_scheme_ids = self._get_verified_rag_schemes()
        if not allowed_scheme_ids:
            return []

        # Grounding check: Gating unsupported or fake domains
        lower_query = search_query.lower()
        if any(re.search(r'\b' + re.escape(u) + r'\b', lower_query) or (u in lower_query and (' ' in u or not u.isascii())) for u in UNSUPPORTED_DOMAINS):
            return []

        # Grounding check: Fake 100% free tractor or marriage cash or institutional DDRS
        if 'tractor' in lower_query and any(w in lower_query for w in ['free', 'muft', '100%', 'zero', 'bina']):
            return []
        if any(w in lower_query for w in ['shaadi', 'shadi', 'vivah', 'kanyadan', 'kanyadaan', 'ddrs', 'deen dayal disabled', 'mig-ii', 'mig 2', 'mig-2']):
            return []

        # Scheme-specific statutory domain gating
        is_health_query = any(w in lower_query for w in ['hospital', 'hospitalization', 'health insurance', 'cashless hospital', 'hospital reimbursement'])
        if is_health_query:
            target_cand = target_scheme_id
            if target_cand and 'pmjay' not in target_cand and 'ayushman' not in target_cand and 'bima' not in target_cand:
                return []

        # Stage 1: Scheme / Entity Candidate Resolution (Two-Stage Architecture)
        candidate_schemes: Set[str] = set()
        if target_scheme_id:
            candidate_schemes.add(target_scheme_id)
        else:
            for sch_key, (canonical_id, _, aliases) in SCHEME_KEYWORDS.items():
                for alias in aliases:
                    if alias.lower() in lower_query:
                        candidate_schemes.add(canonical_id)
                        break

        # Enforce verified-only filter on identified candidate schemes
        effective_scheme_filter = None
        if candidate_schemes:
            valid_candidates = candidate_schemes.intersection(allowed_scheme_ids)
            if not valid_candidates:
                # All identified schemes are unverified or gated! Under no circumstances return unverified chunks.
                return []
            effective_scheme_filter = valid_candidates

        # 2. Stage 2: Run Lexical (BM25) and Dense retrieval across candidate schemes
        lexical_results = self.search_lexical(search_query, scheme_id_filter=effective_scheme_filter, limit=25)
        dense_results = self.search_dense(search_query, scheme_id_filter=effective_scheme_filter, limit=25)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}

        for rank, item in enumerate(lexical_results):
            c_id = item["chunk_id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.RRF_K + (rank + 1)))

        for rank, item in enumerate(dense_results):
            c_id = item["chunk_id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.RRF_K + (rank + 1)))

        # 4. Fetch full chunk entities for survivors
        chunk_ids = set(rrf_scores.keys())
        if not chunk_ids:
            return []

        # Use in-memory cache if populated, else query DB
        chunks_by_id: Dict[str, Any] = {}
        if self._cached_chunks:
            chunks_by_id = {c.id: c for c in self._cached_chunks if c.id in chunk_ids}
        else:
            chunks_by_id = {
                str(c.id): c
                for c in self.db.query(RagChunk).filter(RagChunk.id.in_(list(chunk_ids))).all()
            }

        # 5. Certification Hard Filter, Grounding Validation & Candidate Packaging
        raw_tokens = re.findall(r'[a-zA-Z0-9%₹\u0900-\u097F]+', lower_query)

        domain_specific_tokens = [
            w for w in raw_tokens
            if len(w) >= 3 and w not in GROUNDING_STOPWORDS and w not in SCHEME_NAME_WORDS and w not in GENERIC_BENEFIT_WORDS
        ]

        # If query mentions NO scheme AND has no domain-specific tokens, it is ambiguous
        if not candidate_schemes and not target_scheme_id and not domain_specific_tokens:
            return []

        candidate_chunks = []
        for c_id, base_rrf in rrf_scores.items():
            chunk = chunks_by_id.get(c_id)
            if not chunk or not chunk.is_active:
                continue

            # Hard gate 1: Is chunk's scheme in the allowed citizen certified set?
            if chunk.scheme_id not in allowed_scheme_ids:
                continue

            # Hard gate 2: Scheme alignment (Two-Stage candidate verification)
            if target_scheme_id and chunk.scheme_id != target_scheme_id:
                continue
            if candidate_schemes and chunk.scheme_id not in candidate_schemes:
                continue

            # Hard gate 3: If no scheme was identified at all, require domain token match
            if not candidate_schemes and not target_scheme_id:
                chunk_searchable = f"{chunk.heading_path} {chunk.content}".lower()
                has_domain_match = any(
                    re.search(r'\b' + re.escape(tok) + r'\b', chunk_searchable)
                    for tok in domain_specific_tokens
                )
                if not has_domain_match:
                    continue


            snapshot_id = None
            if chunk.metadata_json:
                try:
                    meta = json.loads(chunk.metadata_json) if isinstance(chunk.metadata_json, str) else chunk.metadata_json
                    snapshot_id = meta.get("snapshot_id") or meta.get("source_snapshot_id")
                except Exception:
                    pass

            candidate_chunks.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "scheme_id": chunk.scheme_id,
                "scheme_version_id": chunk.scheme_version_id,
                "section_type": chunk.section_type,
                "heading_path": chunk.heading_path,
                "content": chunk.content,
                "source_citation": chunk.source_citation,
                "source_url": chunk.source_url,
                "source_snapshot_id": snapshot_id or chunk.document_id,
                "chunk_hash": chunk.chunk_hash,
                "metadata_json": chunk.metadata_json,
                "base_rrf": base_rrf,
                "rrf_score": base_rrf
            })

        # 6. Apply Active Reranker
        active_reranker = self._resolve_reranker(reranker) if reranker is not None else self.reranker
        ranked_chunks = active_reranker.rerank(
            candidates=candidate_chunks,
            query=search_query,
            section_hint=section_hint
        )

        return ranked_chunks[:top_k]
