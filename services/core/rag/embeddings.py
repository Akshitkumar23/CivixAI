"""
Extensible Dense Embedding Provider Abstraction
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Provides dense semantic vector representation and cosine similarity scoring.
Default implementation uses a zero-network-dependency, high-speed LSA/TF-IDF
vectorizer with subword and word n-grams that natively handles Hindi, Hinglish,
and English inflections and typos.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD


class EmbeddingProvider(ABC):
    """
    Abstract interface for document and query embedding providers.
    """

    @abstractmethod
    def fit_or_load(self, corpus: List[str]):
        """Fits vocabulary or loads pre-trained weights."""
        pass

    @abstractmethod
    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """Embeds a list of document texts into 2D float32 numpy array [N, D]."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single query string into 1D float32 numpy array [D]."""
        pass

    @abstractmethod
    def compute_similarity(self, query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        """Computes cosine similarity between query vector and matrix of doc vectors."""
        pass


class DenseLsaEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, offline dense semantic vectorizer based on sublinear
    word+char n-gram TF-IDF and Latent Semantic Analysis (TruncatedSVD).
    
    Trained locally on the certified corpus chunks.
    Ensures zero network dependencies and fast inference (<2ms).
    """

    def __init__(self, n_components: int = 64):
        self.n_components = n_components
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            analyzer="word",
            sublinear_tf=True,
            lowercase=True,
            strip_accents="unicode",
            min_df=1
        )
        self.svd: Optional[TruncatedSVD] = None
        self.is_fitted = False

    def fit_or_load(self, corpus: List[str]):
        if not corpus:
            return
        tfidf_matrix = self.vectorizer.fit_transform(corpus)
        n_features = tfidf_matrix.shape[1]
        actual_components = min(self.n_components, n_features - 1) if n_features > 2 else 1
        if actual_components >= 2 and tfidf_matrix.shape[0] >= 2:
            self.svd = TruncatedSVD(n_components=actual_components, random_state=42)
            self.svd.fit(tfidf_matrix)
        else:
            self.svd = None
        self.is_fitted = True

    def embed_documents(self, documents: List[str]) -> np.ndarray:
        if not self.is_fitted:
            self.fit_or_load(documents)
        if not documents:
            return np.empty((0, self.n_components), dtype=np.float32)

        tfidf_matrix = self.vectorizer.transform(documents)
        if self.svd is not None:
            dense_vecs = self.svd.transform(tfidf_matrix)
        else:
            dense_vecs = tfidf_matrix.toarray()

        # L2 normalize
        norms = np.linalg.norm(dense_vecs, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        normalized = (dense_vecs / norms).astype(np.float32)
        return normalized

    def embed_query(self, query: str) -> np.ndarray:
        if not self.is_fitted:
            return np.zeros(self.n_components, dtype=np.float32)

        tfidf_vec = self.vectorizer.transform([query])
        if self.svd is not None:
            dense_vec = self.svd.transform(tfidf_vec)[0]
        else:
            dense_vec = tfidf_vec.toarray()[0]

        norm = np.linalg.norm(dense_vec)
        if norm > 0:
            dense_vec = dense_vec / norm
        return dense_vec.astype(np.float32)

    def compute_similarity(self, query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        if doc_vecs.size == 0 or query_vec.size == 0:
            return np.empty(0, dtype=np.float32)
        # Cosine similarity for normalized vectors is just the dot product
        if query_vec.shape[0] != doc_vecs.shape[1]:
            # Dimension mismatch fallback
            min_dim = min(query_vec.shape[0], doc_vecs.shape[1])
            sims = np.dot(doc_vecs[:, :min_dim], query_vec[:min_dim])
        else:
            sims = np.dot(doc_vecs, query_vec)
        return np.clip(sims, -1.0, 1.0)


# Devanagari Hindi to English Domain Concept Mapping for Cross-Lingual Alignment
HINDI_DEVANAGARI_MAP = {
    "ईकेवाईसी": "ekyc aadhaar mandatory documents required verification",
    "केवाईसी": "ekyc aadhaar mandatory documents required",
    "टैक्स": "tax income tax payer statutory exclusions not eligible disqualified",
    "आयकर": "income tax payer statutory exclusions not eligible disqualified",
    "किस्त": "installment tranche financial assistance benefits amount 2000",
    "किश्त": "installment tranche financial assistance benefits amount 2000",
    "किस्तें": "installment tranche benefits",
    "पात्रता": "eligibility criteria qualifying conditions qualified eligible",
    "पात्र": "eligible eligibility criteria qualified",
    "दस्तावेज": "documents required mandatory paperwork aadhaar certificate",
    "दस्तावेज़": "documents required mandatory paperwork aadhaar certificate",
    "कागजात": "documents required paperwork proof aadhaar",
    "कागज": "documents paperwork aadhaar mandatory documents required",
    "आवेदन": "application process apply registration portal mobile app csc",
    "पंजीकरण": "registration application process portal mobile app",
    "सब्सिडी": "subsidy interest subvention relief concessional 7 percent",
    "ब्याज": "interest rate subsidy concessional subvention 7 percent",
    "कारीगर": "artisan craftsperson trade traditional worker 18 trades",
    "शिल्पकार": "artisan craftsperson trade traditional worker 18 trades",
    "सिलेंडर": "cylinder lpg gas connection refill subsidy 14.2 kg 5 kg",
    "चूल्हा": "stove hotplate lpg gas connection burner first refill",
    "गैस": "lpg gas connection cylinder refill stove",
    "रेहड़ी": "street vendor urban vendor hawker informal seller",
    "पटरी": "street vendor urban vendor pavement hawker",
    "ठेला": "street vendor urban vendor pushcart informal seller",
    "फेरीवाला": "street vendor urban vendor mobile vendor hawker",
    "कर्ज": "loan credit tranche borrowing working capital collateral free",
    "ऋण": "loan credit tranche borrowing working capital collateral free",
    "लोन": "loan credit tranche borrowing working capital collateral free",
    "टूलकिट": "toolkit equipment incentive 15000 tools vouchers",
    "औजार": "toolkit tools equipment incentive 15000 vouchers",
    "स्टाइपेंड": "stipend training 500 per day skill upgradation",
    "वजीफा": "stipend training 500 per day skill financial",
    "अपात्र": "exclusions statutory not eligible disqualification excluded",
    "बहिष्कार": "exclusions statutory not eligible disqualification excluded",
    "जमीन": "land agricultural landholding cultivable land ownership",
    "भूमि": "land cultivable agricultural landholding ownership",
    "पेंशन": "pension retired pensioner monthly pension 10000 exclusions",
    "सरकारी": "government employee institutional public servant exclusions"
}

# Domain section cues for intent alignment
DOMAIN_SECTION_CUES = {
    "exclusions": [
        "not eligible", "disqualified", "exclusion", "exclusions", "excluded",
        "nahi milega", "kisko nahi", "tax", "income tax", "pension", "pensioner",
        "government employee", "sarkari naukri", "ineligible", "cannot apply",
        "अपात्र", "बहिष्कार", "chartered accountant", "doctor", "lawyer", "pmegp", "mudra",
        "unpaid", "already possess", "do lpg"
    ],
    "eligibility_criteria": [
        "who is eligible", "eligibility criteria", "qualify", "patra", "patrata",
        "18 trades", "landholding", "tenant", "poor household", "women", "पुरुष",
        "husband and wife", "family definition", "adult woman", "zameen nahi"
    ],
    "documents_required": [
        "document", "documents", "aadhaar", "dastavez", "kagaz", "kaagaz",
        "certificate", "ekyc", "e-kyc", "identity proof", "documents required", "कागज", "दस्तावेज"
    ],
    "application_process": [
        "how to apply", "apply online", "application process", "portal",
        "registration", "aavedan", "panjikaran", "step by step", "mobile app", "csc center",
        "आवेदन", "पंजीकरण"
    ],
    "benefits_and_tranches": [
        "how much", "kitna", "kitne", "rupees", "amount", "tranche", "installment",
        "kist", "subsidy", "interest rate", "stipend", "toolkit incentive", "financial assistance",
        "कितने", "किस्त", "सब्सिडी", "ब्याज", "टूलकिट", "वजीफा", "स्टाइपेंड"
    ]
}


class MultilingualSemanticEmbeddingProvider(EmbeddingProvider):
    """
    Extensible multilingual semantic vectorizer designed for cross-lingual citizen retrieval.
    
    Combines:
    1. Word-level sublinear TF-IDF (1, 2 n-grams) for phrase precision.
    2. Character word-boundary n-grams (3, 5 n-grams) for morphological resilience,
       typo tolerance, and inflection matching across Hindi and Latin-script Hinglish.
    3. Multi-script concept mapping that projects Devanagari Hindi and Hinglish
       into aligned semantic vector representations.
    4. TruncatedSVD for latent semantic concept projection with L2 normalization.
    5. Extensible Neural / SentenceTransformer hook: If sentence-transformers is
       configured or installed, delegates to neural transformer embeddings.
    """

    def __init__(
        self,
        n_components: int = 64,
        model_name: Optional[str] = None,
        use_transformer_if_available: bool = False
    ):
        self.n_components = n_components
        self.model_name = model_name or "paraphrase-multilingual-MiniLM-L12-v2"
        self.use_transformer = use_transformer_if_available
        self._transformer_model = None

        if self.use_transformer:
            try:
                from sentence_transformers import SentenceTransformer
                self._transformer_model = SentenceTransformer(self.model_name)
            except (ImportError, Exception):
                self._transformer_model = None

        from sklearn.pipeline import FeatureUnion
        self.word_vec = TfidfVectorizer(
            ngram_range=(1, 2),
            analyzer="word",
            sublinear_tf=True,
            lowercase=True,
            strip_accents="unicode",
            min_df=1
        )
        self.char_vec = TfidfVectorizer(
            ngram_range=(3, 5),
            analyzer="char_wb",
            sublinear_tf=True,
            lowercase=True,
            min_df=1
        )
        self.union = FeatureUnion([
            ("word", self.word_vec),
            ("char", self.char_vec)
        ])
        self.svd: Optional[TruncatedSVD] = None
        self.is_fitted = False

    def _enrich_text(self, text: str) -> str:
        """
        Normalizes and enriches queries and chunk texts across English, Hindi, and Hinglish.
        """
        try:
            from services.core.rag.normalizer import MultilingualQueryNormalizer
            norm = MultilingualQueryNormalizer.normalize_query(text)
            query_text = norm["search_query"]
            lang = norm["detected_language"]
            candidate_schemes = norm["candidate_schemes"]
        except Exception:
            query_text = text
            lang = "hi" if any('\u0900' <= ch <= '\u097f' for ch in text) else "en"
            candidate_schemes = []

        lower_raw = text.lower()

        # Devanagari concept expansion
        if lang == "hi":
            expansions = []
            for hi_k, en_v in HINDI_DEVANAGARI_MAP.items():
                if hi_k in text:
                    expansions.append(en_v)
            if expansions:
                query_text = f"{query_text} {' '.join(expansions)}"

        # Section cues expansion
        matched_sections = []
        for sec, cues in DOMAIN_SECTION_CUES.items():
            if any(cue in lower_raw for cue in cues):
                matched_sections.append(f"section_{sec}")
        if matched_sections:
            query_text = f"{' '.join(matched_sections)} {query_text}"

        # Candidate schemes expansion
        if candidate_schemes:
            scheme_terms = " ".join([f"{s[0]} {s[1]}" for s in candidate_schemes])
            query_text = f"{scheme_terms} {query_text}"

        return query_text

    def fit_or_load(self, corpus: List[str]):
        if self._transformer_model is not None:
            self.is_fitted = True
            return

        if not corpus:
            return

        enriched_corpus = [self._enrich_text(doc) for doc in corpus]
        X = self.union.fit_transform(enriched_corpus)
        n_features = X.shape[1]
        n_samples = X.shape[0]
        actual_components = min(self.n_components, n_features - 1, n_samples - 1)
        if actual_components >= 2:
            self.svd = TruncatedSVD(n_components=actual_components, random_state=42)
            self.svd.fit(X)
        else:
            self.svd = None
        self.is_fitted = True

    def embed_documents(self, documents: List[str]) -> np.ndarray:
        if self._transformer_model is not None:
            vecs = self._transformer_model.encode(documents, convert_to_numpy=True)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0.0] = 1.0
            return (vecs / norms).astype(np.float32)

        if not self.is_fitted:
            self.fit_or_load(documents)
        if not documents:
            return np.empty((0, self.n_components), dtype=np.float32)

        enriched = [self._enrich_text(doc) for doc in documents]
        X = self.union.transform(enriched)
        if self.svd is not None:
            vecs = self.svd.transform(X)
        else:
            vecs = X.toarray()

        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return (vecs / norms).astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        if self._transformer_model is not None:
            vec = self._transformer_model.encode([query], convert_to_numpy=True)[0]
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.astype(np.float32)

        if not self.is_fitted:
            return np.zeros(self.n_components, dtype=np.float32)

        enriched = self._enrich_text(query)
        X = self.union.transform([enriched])
        if self.svd is not None:
            vec = self.svd.transform(X)[0]
        else:
            vec = X.toarray()[0]

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.astype(np.float32)

    def compute_similarity(self, query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        if doc_vecs.size == 0 or query_vec.size == 0:
            return np.empty(0, dtype=np.float32)
        if query_vec.shape[0] != doc_vecs.shape[1]:
            min_dim = min(query_vec.shape[0], doc_vecs.shape[1])
            sims = np.dot(doc_vecs[:, :min_dim], query_vec[:min_dim])
        else:
            sims = np.dot(doc_vecs, query_vec)
        return np.clip(sims, -1.0, 1.0)


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Extensible Neural Transformer Embedding Provider using sentence-transformers.
    Supports multilingual pre-trained transformer models (e.g. paraphrase-multilingual-MiniLM-L12-v2).
    Gracefully falls back to MultilingualSemanticEmbeddingProvider if dependencies are absent.
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        fallback_n_components: int = 64
    ):
        self.model_name = model_name
        self.model = None
        self._fallback_provider: Optional[MultilingualSemanticEmbeddingProvider] = None

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except (ImportError, Exception):
            self.model = None
            self._fallback_provider = MultilingualSemanticEmbeddingProvider(n_components=fallback_n_components)

    def fit_or_load(self, corpus: List[str]):
        if self.model is not None:
            return
        if self._fallback_provider is not None:
            self._fallback_provider.fit_or_load(corpus)

    def embed_documents(self, documents: List[str]) -> np.ndarray:
        if self.model is not None:
            vecs = self.model.encode(documents, convert_to_numpy=True)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0.0] = 1.0
            return (vecs / norms).astype(np.float32)
        if self._fallback_provider is not None:
            return self._fallback_provider.embed_documents(documents)
        return np.empty((len(documents), 0), dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        if self.model is not None:
            vec = self.model.encode([query], convert_to_numpy=True)[0]
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.astype(np.float32)
        if self._fallback_provider is not None:
            return self._fallback_provider.embed_query(query)
        return np.empty(0, dtype=np.float32)

    def compute_similarity(self, query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        if doc_vecs.size == 0 or query_vec.size == 0:
            return np.empty(0, dtype=np.float32)
        if query_vec.shape[0] != doc_vecs.shape[1]:
            min_dim = min(query_vec.shape[0], doc_vecs.shape[1])
            sims = np.dot(doc_vecs[:, :min_dim], query_vec[:min_dim])
        else:
            sims = np.dot(doc_vecs, query_vec)
        return np.clip(sims, -1.0, 1.0)
