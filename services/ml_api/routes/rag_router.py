"""
CivixAI RAG & Grounded Search API Router (Phase 4)
Verified-Only Hybrid Retrieval, Grounded Evidence QA & Citation Enforcement.

Endpoints:
- POST /v1/search: Hybrid search across certified scheme chunks.
- POST /v1/rag/query: Grounded query with intent routing, synthesis & citations.
- POST /v1/rag/eligibility-explain: Deterministic eligibility with official grounding.
- GET  /v1/rag/schemes: Certified schemes indexed in RAG.
- GET  /v1/rag/sources/{source_id}: Source metadata & snapshot hash verification.
"""
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.core.database import get_db, Scheme, SchemeVersion, SchemeCertificationDossier
from services.core.database.models import RagDocument, RagChunk, SourceDocument
from services.core.rag import (
    FtsManager, HybridRetriever, PgVectorRetriever, GroundedAnswerEngine,
    MultilingualQueryNormalizer, IntentRouter
)

router = APIRouter(tags=["RAG & Verified Evidence Search"])

# Lazy singleton retriever cache
_fts_manager: Optional[FtsManager] = None
_retriever: Optional[Union[HybridRetriever, PgVectorRetriever]] = None

def get_rag_components(db: Session = Depends(get_db)):
    global _fts_manager, _retriever
    if _fts_manager is None:
        db_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "civix.db"
        _fts_manager = FtsManager(db_path)
    if _retriever is None:
        try:
            bind = db.get_bind()
            if bind is not None and bind.dialect.name == "postgresql":
                _retriever = PgVectorRetriever(db=db, fts_manager=_fts_manager)
            else:
                _retriever = HybridRetriever(db, _fts_manager)
                _retriever.refresh_dense_index()
        except Exception:
            _retriever = HybridRetriever(db, _fts_manager)
            _retriever.refresh_dense_index()
    return _fts_manager, _retriever


# ── Request / Response Schemas ────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query in English, Hindi, or Hinglish")
    scheme_id: Optional[str] = Field(None, description="Optional target certified scheme ID filter")
    section_type: Optional[str] = Field(None, description="Optional section filter (eligibility_criteria, exclusions, benefits_and_tranches, documents_required, application_process)")
    limit: int = Field(default=5, ge=1, le=20)


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or eligibility inquiry")
    user_facts: Optional[Dict[str, Any]] = Field(None, description="Optional profile facts for deterministic eligibility check")
    target_scheme_id: Optional[str] = Field(None, description="Optional target scheme ID")


class EligibilityExplainRequest(BaseModel):
    scheme_id: str = Field(..., description="Target certified scheme ID")
    user_facts: Dict[str, Any] = Field(..., description="Applicant profile facts for deterministic evaluation")
    query: Optional[str] = Field(None, description="Optional natural language inquiry")


# ── Route Handlers ────────────────────────────────────────────────────────────

@router.post("/v1/search")
def search_certified_corpus(
    req: SearchRequest,
    db: Session = Depends(get_db),
    rag_comps = Depends(get_rag_components)
):
    """
    Hybrid search across official certified scheme chunks.
    Enforces the RAG certification gate: uncertified schemes yield 0 results.
    """
    fts_mgr, retriever = rag_comps
    start_time = time.perf_counter()

    norm = MultilingualQueryNormalizer.normalize_query(req.query)
    target_scheme = req.scheme_id or norm.get("primary_scheme_id")

    hits = retriever.retrieve(
        search_query=norm["search_query"],
        target_scheme_id=target_scheme,
        section_hint=req.section_type,
        top_k=req.limit
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "query": req.query,
        "normalized_query": norm["normalized_query"],
        "detected_language": norm["detected_language"],
        "total": len(hits),
        "latency_ms": round(elapsed_ms, 2),
        "results": hits
    }


@router.post("/v1/rag/query")
def answer_rag_query(
    req: RagQueryRequest,
    db: Session = Depends(get_db),
    rag_comps = Depends(get_rag_components)
):
    """
    Grounded question answering with intent routing, prompt injection defense,
    deterministic eligibility supremacy, and strict citation enforcement.
    """
    fts_mgr, retriever = rag_comps
    engine = GroundedAnswerEngine(db, retriever)

    result = engine.answer_query(
        raw_query=req.query,
        user_facts=req.user_facts,
        target_scheme_id=req.target_scheme_id
    )

    return result


@router.post("/v1/rag/eligibility-explain")
def explain_eligibility_with_evidence(
    req: EligibilityExplainRequest,
    db: Session = Depends(get_db),
    rag_comps = Depends(get_rag_components)
):
    """
    Evaluates deterministic eligibility for a scheme and grounds the reasoning
    in official statutory evidence chunks.
    """
    fts_mgr, retriever = rag_comps
    engine = GroundedAnswerEngine(db, retriever)

    query_text = req.query or f"Am I eligible for {req.scheme_id}?"
    result = engine.answer_query(
        raw_query=query_text,
        user_facts=req.user_facts,
        target_scheme_id=req.scheme_id
    )

    return result


@router.get("/v1/rag/schemes")
def get_rag_certified_schemes(db: Session = Depends(get_db)):
    """
    Lists schemes currently certified and indexed for citizen RAG.
    """
    active_dossiers = db.query(SchemeCertificationDossier).filter(
        SchemeCertificationDossier.is_active == True,
        SchemeCertificationDossier.semantic_review_status == "certified",
        SchemeCertificationDossier.audience_type != "NGO_GRANT"
    ).all()

    schemes_data = []
    for d in active_dossiers:
        scheme = db.query(Scheme).filter(Scheme.id == d.scheme_id).first()
        chunks_count = db.query(RagChunk).filter(
            RagChunk.scheme_id == d.scheme_id,
            RagChunk.is_active == True
        ).count()

        schemes_data.append({
            "scheme_id": d.scheme_id,
            "scheme_name": scheme.canonical_name if scheme else d.scheme_id,
            "applicant_type": d.applicant_type,
            "beneficiary_type": d.beneficiary_type,
            "audience_type": d.audience_type,
            "latest_source_reference": d.latest_source_reference,
            "certified_at": d.certified_at.isoformat() if d.certified_at else None,
            "certification_hash": d.certification_hash,
            "dossier_id": d.id,
            "indexed_chunks_count": chunks_count,
            "is_rag_certified": True
        })

    return {
        "rag_certified_schemes_count": len(schemes_data),
        "schemes": schemes_data
    }


@router.get("/v1/rag/sources/{source_id}")
def get_rag_source_metadata(source_id: str, db: Session = Depends(get_db)):
    """
    Returns official source document metadata and content verification hash.
    """
    source = db.query(SourceDocument).filter(SourceDocument.id == source_id).first()
    if not source:
        # Fallback to rag_documents
        rag_doc = db.query(RagDocument).filter(RagDocument.id == source_id).first()
        if not rag_doc:
            raise HTTPException(status_code=404, detail=f"Source document '{source_id}' not found")
        return {
            "source_id": rag_doc.id,
            "scheme_id": rag_doc.scheme_id,
            "document_title": rag_doc.document_title,
            "url": rag_doc.source_url,
            "content_hash": rag_doc.content_hash,
            "doc_type": rag_doc.doc_type,
            "is_active": rag_doc.is_active,
            "created_at": rag_doc.created_at.isoformat() if rag_doc.created_at else None
        }

    return {
        "source_id": source.id,
        "scheme_version_id": source.scheme_version_id,
        "document_title": getattr(source, "document_title", "Official Guideline"),
        "url": source.url,
        "content_hash": source.content_hash,
        "document_type": source.document_type,
        "verification_status": source.verification_status,
        "published_date": str(source.published_date) if source.published_date else None
    }
