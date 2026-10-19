import json
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.core.database import get_db
from services.core.database.models import (
    ProfileSession, ProfileFact, Scheme, SchemeVersion,
    RecommendationRun, RecommendationItem, FeedbackEvent,
    SchemeCertificationDossier
)
from services.core.facts.registry import normalize_profile_to_facts
from services.core.recommendations import RecommendationEngine
from services.core.profiling import QuestionEngine

router = APIRouter(prefix="/v1", tags=["Civix Core v1"])

# ── Pydantic Request/Response Models ──────────────────────────────────────────

class ProfileSessionCreate(BaseModel):
    is_anonymous: bool = True
    facts: Dict[str, Any] = Field(default_factory=dict)

class FactsUpdate(BaseModel):
    facts: Dict[str, Any]

class RecommendationRequest(BaseModel):
    session_id: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    programme_kind: Optional[str] = None  # welfare, loan, insurance
    top_k: int = 50
    source: Optional[str] = None  # CLASSIC, ADAPTIVE, IMPORTED

class FeedbackRequest(BaseModel):
    session_id: Optional[str] = None
    scheme_id: str
    event_type: str  # helpful, not_relevant, apply_click, compare
    reason_code: Optional[str] = None

# ── 1. Profile Sessions & Fact Persistence ────────────────────────────────────

@router.post("/profile-sessions")
def create_profile_session(
    payload: ProfileSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a secure server-side profile session.
    Keeps sensitive demographic data off URL query parameters.
    """
    session_id = str(uuid.uuid4())
    session_obj = ProfileSession(id=session_id, is_anonymous=payload.is_anonymous)
    db.add(session_obj)

    canonical_facts = normalize_profile_to_facts(payload.facts)
    for k, v in canonical_facts.items():
        fact_obj = ProfileFact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            fact_key=k,
            fact_value=json.dumps(v),
            verified=False
        )
        db.add(fact_obj)

    db.commit()
    return {
        "session_id": session_id,
        "facts_count": len(canonical_facts),
        "facts": canonical_facts
    }

from services.core.questionnaire import (
    QuestionnaireOrchestrator, AnswerPayload, SkipPayload, UnknownPayload
)

@router.patch("/profile-sessions/{session_id}/facts")
def update_profile_facts(
    session_id: str,
    payload: FactsUpdate,
    db: Session = Depends(get_db)
):
    session_obj = db.query(ProfileSession).filter_by(id=session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Profile session not found")

    canonical_facts = normalize_profile_to_facts(payload.facts)
    for k, v in canonical_facts.items():
        existing_fact = db.query(ProfileFact).filter_by(session_id=session_id, fact_key=k).first()
        if existing_fact:
            existing_fact.fact_value = json.dumps(v)
            existing_fact.is_skipped = False
            existing_fact.is_unknown = False
        else:
            db.add(ProfileFact(
                id=str(uuid.uuid4()),
                session_id=session_id,
                fact_key=k,
                fact_value=json.dumps(v),
                verified=False
            ))
    db.commit()
    return {"status": "updated", "updated_keys": list(canonical_facts.keys())}

@router.get("/profile-sessions/{session_id}/questionnaire-state")
def get_questionnaire_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Returns the complete, resumable questionnaire state and progress."""
    orchestrator = QuestionnaireOrchestrator(db)
    return orchestrator.get_state(session_id).model_dump()

@router.get("/profile-sessions/{session_id}/next-question")
def get_next_question(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns the next optimal question determined from active rule dependencies.
    """
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.get_state(session_id)
    cq = state.current_question

    return {
        "session_id": session_id,
        "has_next_question": cq is not None and not state.is_completed,
        "next_question": cq.model_dump() if cq else None,
        "is_completed": state.is_completed,
        "progress": state.progress.model_dump(),
        "current_eligible_count": state.progress.current_eligible_schemes_count
    }

from services.core.questionnaire import (
    QuestionnaireOrchestrator, AnswerPayload, SkipPayload, UnknownPayload,
    EditAnswerPayload, PreferNotToSayPayload, RecalculatePayload
)
from services.core.recommendations.benefit_paths import BenefitPathEngine, CitizenGoal
from services.core.applications.checklist_service import (
    ApplicationChecklistService, ApplicationLifecycleStatus
)

@router.post("/profile-sessions/{session_id}/answer")
def answer_question(
    session_id: str,
    payload: AnswerPayload,
    db: Session = Depends(get_db)
):
    """Answers a question and returns updated questionnaire state."""
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.answer_question(
        session_id=session_id,
        fact_key=payload.fact_key,
        value=payload.value,
        scope=payload.scope,
        subject_relation=payload.subject_relation,
        member_index=payload.member_index,
        source=payload.source
    )
    return state.model_dump()

@router.post("/profile-sessions/{session_id}/edit-answer")
def edit_answer(
    session_id: str,
    payload: EditAnswerPayload,
    db: Session = Depends(get_db)
):
    """Explicitly edits an existing answer and recalculates dependencies without clearing history."""
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.edit_answer(
        session_id=session_id,
        fact_key=payload.fact_key,
        value=payload.value,
        subject_relation=payload.subject_relation,
        member_index=payload.member_index,
        source=payload.source
    )
    return state.model_dump()

@router.post("/profile-sessions/{session_id}/skip")
def skip_question(
    session_id: str,
    payload: SkipPayload,
    db: Session = Depends(get_db)
):
    """Skips a question without defaulting it to false."""
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.skip_question(
        session_id=session_id,
        fact_key=payload.fact_key,
        subject_relation=payload.subject_relation,
        member_index=payload.member_index
    )
    return state.model_dump()

@router.post("/profile-sessions/{session_id}/prefer-not-to-say")
def prefer_not_to_say(
    session_id: str,
    payload: PreferNotToSayPayload,
    db: Session = Depends(get_db)
):
    """Explicit privacy choice for sensitive demographic questions; affected schemes stay NEEDS_INFO."""
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.prefer_not_to_say(
        session_id=session_id,
        fact_key=payload.fact_key,
        subject_relation=payload.subject_relation,
        member_index=payload.member_index
    )
    return state.model_dump()

@router.post("/profile-sessions/{session_id}/unknown")
def mark_question_unknown(
    session_id: str,
    payload: UnknownPayload,
    db: Session = Depends(get_db)
):
    """Records an 'I don't know' answer without hard rejection."""
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.mark_unknown(
        session_id=session_id,
        fact_key=payload.fact_key,
        subject_relation=payload.subject_relation,
        member_index=payload.member_index
    )
    return state.model_dump()

@router.post("/profile-sessions/{session_id}/back")
def go_back_question(
    session_id: str,
    subject_relation: str = Query("myself"),
    member_index: int = Query(0),
    db: Session = Depends(get_db)
):
    """Navigates back to the previous question to permit editing."""
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.go_back(
        session_id=session_id,
        subject_relation=subject_relation,
        member_index=member_index
    )
    return state.model_dump()

@router.post("/profile-sessions/{session_id}/recalculate")
def recalculate_questionnaire(
    session_id: str,
    payload: RecalculatePayload,
    db: Session = Depends(get_db)
):
    """Recalculates dependency analysis and remaining questions for the given member."""
    orchestrator = QuestionnaireOrchestrator(db)
    state = orchestrator.recalculate(
        session_id=session_id,
        subject_relation=payload.subject_relation,
        member_index=payload.member_index
    )
    return state.model_dump()

@router.get("/profile-sessions/{session_id}/recommendation-preview")
def get_recommendation_preview(
    session_id: str,
    subject_relation: str = Query("myself"),
    member_index: int = Query(0),
    db: Session = Depends(get_db)
):
    """Returns real-time deterministic eligibility preview for current session facts."""
    orchestrator = QuestionnaireOrchestrator(db)
    return orchestrator.get_recommendation_preview(
        session_id=session_id,
        subject_relation=subject_relation,
        member_index=member_index
    )

def compute_profile_hash(facts: dict) -> str:
    sorted_fact_keys = sorted(facts.keys())
    fact_str = ",".join(f"{k}={facts[k]}" for k in sorted_fact_keys)
    return hashlib.sha256(fact_str.encode("utf-8")).hexdigest()[:16]

@router.post("/recommendations")
def generate_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    facts = {}
    session_id = request.session_id

    if session_id:
        session_obj = db.query(ProfileSession).filter_by(id=session_id).first()
        if session_obj:
            for f in session_obj.facts:
                try:
                    facts[f.fact_key] = json.loads(f.fact_value)
                except Exception:
                    facts[f.fact_key] = f.fact_value
        else:
            session_obj = ProfileSession(id=session_id, is_anonymous=True)
            db.add(session_obj)
            db.flush()
    else:
        session_id = str(uuid.uuid4())
        session_obj = ProfileSession(id=session_id, is_anonymous=True)
        db.add(session_obj)
        db.flush()

    if request.profile:
        normalized = normalize_profile_to_facts(request.profile)
        facts.update(normalized)
        for k, v in facts.items():
            existing_fact = db.query(ProfileFact).filter_by(session_id=session_id, fact_key=k).first()
            if existing_fact:
                existing_fact.fact_value = json.dumps(v)
            else:
                db.add(ProfileFact(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    fact_key=k,
                    fact_value=json.dumps(v),
                    verified=True,
                    source="profile_submission"
                ))
        db.flush()

    sorted_fact_keys = sorted(facts.keys())
    profile_hash = compute_profile_hash(facts)

    engine = RecommendationEngine(db)
    result = engine.evaluate_profile(
        facts=facts,
        session_id=session_id,
        programme_kind=request.programme_kind,
        top_k=request.top_k
    )

    result["session_id"] = session_id
    result["profile_hash"] = profile_hash
    result["normalized_fact_keys"] = sorted_fact_keys
    result["source"] = request.source or ("ADAPTIVE" if (request.session_id and not request.profile) else "CLASSIC")

    return result

@router.get("/recommendations/{run_id}")
def get_recommendation_snapshot(
    run_id: str,
    db: Session = Depends(get_db)
):
    run_record = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run_record:
        raise HTTPException(status_code=404, detail="Recommendation snapshot not found")

    items = []
    for it in run_record.items:
        items.append({
            "scheme_id": it.scheme_id,
            "eligibility_status": it.eligibility_status,
            "confidence_score": it.confidence_score,
            "application_readiness": it.application_readiness,
            "rank_score": it.rank_score,
            "reasons": json.loads(it.reasons_json) if it.reasons_json else [],
            "missing_facts": json.loads(it.missing_facts_json) if it.missing_facts_json else []
        })

    return {
        "run_id": run_record.id,
        "created_at": run_record.created_at.isoformat() if run_record.created_at else None,
        "total_considered": run_record.total_considered,
        "total_eligible": run_record.total_eligible,
        "items": items
    }

# ── 3. Scheme Catalogue & Source Evidence ─────────────────────────────────────

@router.get("/schemes")
def list_schemes(
    programme_kind: Optional[str] = Query(None, description="welfare, loan, or insurance"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Scheme).filter(Scheme.is_active == True)
    if programme_kind:
        query = query.filter(Scheme.programme_kind == programme_kind)

    total = query.count()
    schemes = query.offset(offset).limit(limit).all()

    items = []
    for s in schemes:
        latest_version = s.versions[0] if s.versions else None
        items.append({
            "scheme_id": s.id,
            "scheme_name": s.canonical_name,
            "level": s.scheme_level,
            "programme_kind": s.programme_kind,
            "popularity_score": s.popularity_score,
            "summary": latest_version.summary if latest_version else "",
            "application_url": latest_version.application_url if latest_version else "",
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }

@router.get("/schemes/{scheme_id}")
def get_scheme_details(
    scheme_id: str,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter_by(id=scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    latest_version = scheme.versions[0] if scheme.versions else None

    # Active Certification Dossier metadata
    dossier = db.query(SchemeCertificationDossier).filter(
        SchemeCertificationDossier.scheme_id == scheme.id,
        SchemeCertificationDossier.is_active == True
    ).order_by(SchemeCertificationDossier.certified_at.desc()).first()

    dossier_data = None
    if dossier:
        dossier_data = {
            "dossier_id": dossier.id,
            "certified_at": dossier.certified_at.isoformat() if dossier.certified_at else None,
            "certified_by": dossier.certified_by,
            "semantic_review_status": dossier.semantic_review_status,
            "completeness_status": dossier.completeness_status,
            "currentness_status": dossier.currentness_status,
            "lifecycle_status": dossier.lifecycle_status,
            "last_currentness_check": dossier.last_currentness_check.isoformat() if dossier.last_currentness_check else None,
            "currentness_check_source": dossier.currentness_check_source or "Official Gazette & Ministry Guidelines",
            "is_certified": True
        }

    rules_data = []
    docs_data = []
    benefits_data = []
    sources_data = []

    if latest_version:
        for r in latest_version.rules:
            rules_data.append({
                "fact_key": r.fact_key,
                "operator": r.operator,
                "expected_value": r.expected_value,
                "mandatory": r.mandatory,
                "reason_code": r.reason_code,
                "rule_scope": getattr(r, "rule_scope", "applicant_eligibility")
            })
        for d in latest_version.documents:
            docs_data.append({
                "document_type": d.document_type,
                "is_mandatory": d.is_mandatory
            })
        for b in latest_version.benefits:
            benefits_data.append({
                "benefit_type": b.benefit_type,
                "fixed_amount": b.fixed_amount,
                "description": b.description
            })
        for s in latest_version.sources:
            sources_data.append({
                "url": s.url,
                "document_title": s.document_title or scheme.canonical_name,
                "publisher": s.publisher or "Government of India",
                "trust_level": s.trust_level or "B",
                "verification_status": s.verification_status or "source_verified"
            })

    # If citizen session_id is provided, evaluate this specific scheme for the citizen
    user_match = None
    if session_id:
        session_obj = db.query(ProfileSession).filter_by(id=session_id).first()
        if session_obj:
            facts = {}
            for f in session_obj.facts:
                try:
                    facts[f.fact_key] = json.loads(f.fact_value)
                except Exception:
                    facts[f.fact_key] = f.fact_value
            engine = RecommendationEngine(db)
            eval_res = engine.evaluate_profile(facts=facts, session_id=session_id, top_k=100)
            all_eval_items = (
                eval_res.get("authoritative_pool", {}).get("eligible", []) +
                eval_res.get("authoritative_pool", {}).get("needs_info", []) +
                eval_res.get("authoritative_pool", {}).get("needs_verification", []) +
                eval_res.get("authoritative_pool", {}).get("not_eligible", []) +
                eval_res.get("discovery_pool", [])
            )
            for it in all_eval_items:
                if it["scheme_id"] == scheme_id:
                    user_match = {
                        "eligibility_status": it["eligibility_status"],
                        "reasons": it["reasons"],
                        "missing_facts": it["missing_facts"],
                        "path_to_eligibility": it["path_to_eligibility"],
                        "application_readiness": it["application_readiness"],
                        "readiness_breakdown": it.get("readiness_breakdown", []),
                        "criteria_met_count": it.get("criteria_met_count", 0),
                        "criteria_total_count": it.get("criteria_total_count", 1),
                        "criteria_progress_pct": it.get("criteria_progress_pct", 0),
                    }
                    break

    state_rule = next((r for r in rules_data if r["fact_key"] == "location.state"), None)
    applicable_states = state_rule["expected_value"] if state_rule else ("All India / Central Sector" if scheme.scheme_level == "Central" else "Central")

    return {
        "scheme_id": scheme.id,
        "scheme_name": scheme.canonical_name,
        "scheme_level": scheme.scheme_level,
        "programme_kind": scheme.programme_kind,
        "status": scheme.status,
        "ministry": scheme.authority.name if scheme.authority else "Government of India",
        "category": scheme.category.name if scheme.category else "General",
        "applicable_states": applicable_states,
        "summary": latest_version.summary if latest_version else "",
        "description": latest_version.description if latest_version else "",
        "application_url": latest_version.application_url if latest_version else "",
        "source_url": latest_version.source_url if latest_version else "",
        "processing_time": latest_version.processing_time if latest_version else "",
        "rules": rules_data,
        "documents": docs_data,
        "benefits": benefits_data,
        "sources": sources_data,
        "certification_dossier": dossier_data,
        "user_match": user_match
    }

@router.get("/schemes/{scheme_id}/provenance")
def get_scheme_provenance(
    scheme_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns full legal provenance, source documents, trust levels, and verification statuses.
    """
    scheme = db.query(Scheme).filter_by(id=scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    latest_version = scheme.versions[0] if scheme.versions else None
    if not latest_version:
        raise HTTPException(status_code=404, detail="No versions available for scheme")

    sources_data = []
    for s in latest_version.sources:
        sources_data.append({
            "id": s.id,
            "url": s.url,
            "document_title": s.document_title,
            "publisher": s.publisher,
            "source_fragment": s.source_fragment,
            "trust_level": s.trust_level,
            "verification_status": s.verification_status,
            "freshness_status": s.freshness_status,
            "published_date": s.published_date.isoformat() if s.published_date else None,
            "effective_from": s.effective_from.isoformat() if s.effective_from else None,
            "effective_to": s.effective_to.isoformat() if s.effective_to else None,
        })

    rules_provenance = []
    for r in latest_version.rules:
        rules_provenance.append({
            "id": r.id,
            "fact_key": r.fact_key,
            "operator": r.operator,
            "expected_value": r.expected_value,
            "rule_expression": json.loads(r.rule_expression) if r.rule_expression else None,
            "mandatory": r.mandatory,
            "reason_code": r.reason_code,
            "verification_status": r.verification_status,
            "source_fragment": r.source_fragment,
            "source_evidence_id": r.source_evidence_id,
        })

    return {
        "scheme_id": scheme.id,
        "scheme_name": scheme.canonical_name,
        "version_id": latest_version.id,
        "version_number": latest_version.version_number,
        "verification_status": latest_version.verification_status,
        "review_notes": latest_version.review_notes,
        "reviewed_by": latest_version.reviewed_by,
        "sources": sources_data,
        "rules": rules_provenance,
    }

@router.get("/facts/ranked")
def get_ranked_facts(
    session_id: Optional[str] = None,
    top_n: int = 10,
    db: Session = Depends(get_db)
):
    """
    Ranks missing facts by their ability to unlock and discriminate active schemes.
    """
    from services.core.facts.dependencies import FactDependencyEngine
    engine = RecommendationEngine(db)
    candidates = engine.candidate_service.get_candidates(limit=200)

    current_facts = {}
    if session_id:
        session_obj = db.query(ProfileSession).filter_by(id=session_id).first()
        if session_obj:
            for f in session_obj.facts:
                try:
                    current_facts[f.fact_key] = json.loads(f.fact_value)
                except Exception:
                    current_facts[f.fact_key] = f.fact_value

    dep_engine = FactDependencyEngine(candidates)
    ranked = dep_engine.rank_missing_facts(current_facts, top_n=top_n)
    return {
        "session_id": session_id,
        "ranked_facts": ranked
    }

# ── 4. Feedback Logging ───────────────────────────────────────────────────────

@router.post("/feedback")
def submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db)
):
    event = FeedbackEvent(
        id=str(uuid.uuid4()),
        session_id=payload.session_id,
        scheme_id=payload.scheme_id,
        event_type=payload.event_type,
        reason_code=payload.reason_code
    )
    db.add(event)
    db.commit()
    return {"status": "recorded", "event_id": event.id}

# ── 5. Benefit Paths & Action Plans ──────────────────────────────────────────

class SynthesizePathwayRequest(BaseModel):
    goal_id: str
    session_id: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None

@router.get("/benefit-paths/goals")
def list_benefit_path_goals(
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Detects and returns recommended multi-programme citizen goals."""
    facts = {}
    if session_id:
        orchestrator = QuestionnaireOrchestrator(db)
        facts = orchestrator.get_session_data(session_id)["facts"]
    engine = BenefitPathEngine(db)
    return {
        "recommended_goals": engine.detect_recommended_goals(facts)
    }

@router.post("/benefit-paths/synthesize")
def synthesize_benefit_pathway(
    payload: SynthesizePathwayRequest,
    db: Session = Depends(get_db)
):
    """Synthesizes structured multi-programme support pathways based on structured taxonomy and citizen goals."""
    facts = payload.profile or {}
    evaluated = None
    if payload.session_id:
        orchestrator = QuestionnaireOrchestrator(db)
        data = orchestrator.get_session_data(payload.session_id)
        if not facts:
            facts = data["facts"]
        preview = orchestrator.get_recommendation_preview(payload.session_id)
        evaluated = preview.get("ranked_schemes")

    engine = BenefitPathEngine(db)
    pathway = engine.synthesize_pathway(
        goal_id=payload.goal_id,
        facts=facts,
        evaluated_schemes=evaluated
    )
    return pathway.model_dump()

# ── 6. Application Tracker & Checklist ────────────────────────────────────────

class CreateTrackerRequest(BaseModel):
    session_id: str
    scheme_id: str
    scheme_name: Optional[str] = None
    initial_status: ApplicationLifecycleStatus = ApplicationLifecycleStatus.INTERESTED

class TransitionStatusRequest(BaseModel):
    new_status: ApplicationLifecycleStatus
    notes: Optional[str] = None
    external_ref_number: Optional[str] = None

_global_checklist_service: Optional[ApplicationChecklistService] = None

def get_checklist_service(db: Session = Depends(get_db)) -> ApplicationChecklistService:
    global _global_checklist_service
    if _global_checklist_service is None:
        _global_checklist_service = ApplicationChecklistService(db)
    _global_checklist_service.db = db
    return _global_checklist_service

@router.post("/applications/trackers")
def create_application_tracker(
    payload: CreateTrackerRequest,
    service: ApplicationChecklistService = Depends(get_checklist_service)
):
    """Creates a new application tracking lifecycle entry."""
    tracker = service.create_application_tracker(
        session_id=payload.session_id,
        scheme_id=payload.scheme_id,
        scheme_name=payload.scheme_name,
        initial_status=payload.initial_status
    )
    return tracker.model_dump()

@router.post("/applications/trackers/{application_id}/transition")
def transition_application_status(
    application_id: str,
    payload: TransitionStatusRequest,
    service: ApplicationChecklistService = Depends(get_checklist_service)
):
    """Transitions tracker through the application lifecycle state machine."""
    try:
        tracker = service.transition_status(
            application_id=application_id,
            new_status=payload.new_status,
            notes=payload.notes,
            external_ref_number=payload.external_ref_number
        )
        return tracker.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/applications/schemes/{scheme_id}/checklist")
def get_scheme_checklist_and_steps(
    scheme_id: str,
    session_id: Optional[str] = None,
    service: ApplicationChecklistService = Depends(get_checklist_service),
    db: Session = Depends(get_db)
):
    """Returns official versioned steps, official portal verification, and document checklist."""
    facts = {}
    if session_id:
        orchestrator = QuestionnaireOrchestrator(db)
        facts = orchestrator.get_session_data(session_id)["facts"]

    steps = service.get_official_steps(scheme_id)
    checklist = service.get_document_checklist(scheme_id, facts)
    return {
        "scheme_id": scheme_id,
        "official_steps": [s.model_dump() for s in steps],
        "document_checklist": [c.model_dump() for c in checklist]
    }

@router.post("/applications/schemes/{scheme_id}/safe-autofill")
def generate_safe_offline_autofill(
    scheme_id: str,
    facts_payload: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    service: ApplicationChecklistService = Depends(get_checklist_service),
    db: Session = Depends(get_db)
):
    """Generates safe offline autofill draft mapping and printable checklist without third-party web submissions."""
    facts = facts_payload or {}
    if session_id and not facts:
        orchestrator = QuestionnaireOrchestrator(db)
        facts = orchestrator.get_session_data(session_id)["facts"]

    draft = service.generate_safe_offline_autofill_draft(scheme_id, facts)
    return draft.model_dump()
