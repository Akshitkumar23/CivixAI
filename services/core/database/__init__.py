"""
Database package for CivixAI Core
"""
from .connection import get_engine, init_db
from .session import get_db, SessionLocal
from .models import (
    Base, Scheme, SchemeVersion, Authority, Category,
    EligibilityRule, Benefit, DocumentRequirement, SourceDocument,
    ProfileSession, ProfileFact, RecommendationRun, RecommendationItem,
    FeedbackEvent, SourceRegistry, SourceSnapshot, IngestionRun,
    SchemeChangeSet, RuleDraft, BenefitDraft, DocumentRequirementDraft,
    AuditLog, SourceConflict, DuplicateCandidate, SchemeCertificationDossier
)

__all__ = [
    "get_engine", "init_db", "get_db", "SessionLocal", "Base",
    "Scheme", "SchemeVersion", "Authority", "Category",
    "EligibilityRule", "Benefit", "DocumentRequirement", "SourceDocument",
    "ProfileSession", "ProfileFact", "RecommendationRun", "RecommendationItem",
    "FeedbackEvent", "SourceRegistry", "SourceSnapshot", "IngestionRun",
    "SchemeChangeSet", "RuleDraft", "BenefitDraft", "DocumentRequirementDraft",
    "AuditLog", "SourceConflict", "DuplicateCandidate", "SchemeCertificationDossier"
]
