"""
CivixAI RAG Engine Package (Phase 4)
Verified-Only Hybrid Retrieval, Grounded RAG, Multilingual Evidence QA & Citation Enforcement.
"""
from services.core.rag.fts_manager import FtsManager
from services.core.rag.embeddings import (
    EmbeddingProvider,
    DenseLsaEmbeddingProvider,
    MultilingualSemanticEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from services.core.rag.chunker import StructureAwareChunker
from services.core.rag.normalizer import MultilingualQueryNormalizer
from services.core.rag.router import IntentRouter
from services.core.rag.retriever import (
    HybridRetriever,
    BaseReranker,
    NoReranker,
    HeuristicReranker,
    SemanticRerankerCandidate,
    SemanticReranker
)
from services.core.rag.pgvector_retriever import PgVectorRetriever
from services.core.rag.indexer import RagIndexingPipeline
from services.core.rag.engine import GroundedAnswerEngine
from services.core.rag.grounding import ClaimGroundingEngine, GroundedClaim, GroundingMetrics
from services.core.rag.privacy import QueryTracePrivacy

__all__ = [
    "FtsManager",
    "EmbeddingProvider",
    "DenseLsaEmbeddingProvider",
    "MultilingualSemanticEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "StructureAwareChunker",
    "MultilingualQueryNormalizer",
    "IntentRouter",
    "HybridRetriever",
    "PgVectorRetriever",
    "BaseReranker",
    "NoReranker",
    "HeuristicReranker",
    "SemanticRerankerCandidate",
    "SemanticReranker",
    "RagIndexingPipeline",
    "GroundedAnswerEngine",
    "ClaimGroundingEngine",
    "GroundedClaim",
    "GroundingMetrics",
    "QueryTracePrivacy",
]
