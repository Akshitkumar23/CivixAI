"""
Questionnaire Domain Models
Pydantic schemas for questions, session state, progress, and user interactions.
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

SubjectRelation = Literal["myself", "parent", "child", "spouse", "other_household_member"]
SensitivityLevel = Literal["normal", "financial", "sensitive"]
InputComponentType = Literal["number", "select", "radio", "boolean", "text", "range"]

class QuestionMetadata(BaseModel):
    fact_key: str
    component_type: InputComponentType
    label_en: str
    label_hi: str
    help_text_en: str = ""
    help_text_hi: str = ""
    why_asked_en: str
    why_asked_hi: str
    allowed_values: Optional[List[Dict[str, str]]] = None # [{"value": "rural", "label_en": "Rural", "label_hi": "ग्रामीण"}]
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sensitivity: SensitivityLevel = "normal"
    scope: str = "applicant" # applicant, spouse, household, child, landholding, business
    can_skip: bool = True
    can_answer_unknown: bool = True
    is_repeatable: bool = False
    validation_regex: Optional[str] = None

class QuestionnaireProgress(BaseModel):
    answered_count: int
    unresolved_relevant_facts_count: int
    estimated_remaining_questions: int
    progress_pct: float
    current_eligible_schemes_count: int
    current_needs_info_schemes_count: int

class QuestionResponse(BaseModel):
    session_id: str
    fact_key: str
    question: QuestionMetadata
    why_asked: str
    affected_schemes_count: int
    progress: QuestionnaireProgress
    can_go_back: bool = False
    is_completed: bool = False
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0

class HouseholdMemberProfile(BaseModel):
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0
    display_name: str = "Primary Applicant"
    consent_given: bool = True
    consent_type: str = "self_declaration"
    consented_at: Optional[str] = None
    answered_count: int = 0

class QuestionnaireState(BaseModel):
    session_id: str
    is_completed: bool = False
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0
    current_question: Optional[QuestionResponse] = None
    answered_facts: Dict[str, Any] = Field(default_factory=dict)
    skipped_facts: List[str] = Field(default_factory=list)
    unknown_facts: List[str] = Field(default_factory=list)
    prefer_not_to_say_facts: List[str] = Field(default_factory=list)
    history: List[str] = Field(default_factory=list)
    progress: QuestionnaireProgress
    household_members: List[HouseholdMemberProfile] = Field(default_factory=list)

class AnswerPayload(BaseModel):
    fact_key: str
    value: Any
    scope: str = "applicant"
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0
    source: str = "self_declared"

class EditAnswerPayload(BaseModel):
    fact_key: str
    value: Any
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0
    source: str = "user_edited"

class SkipPayload(BaseModel):
    fact_key: str
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0

class PreferNotToSayPayload(BaseModel):
    fact_key: str
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0
    reason: Optional[str] = "privacy_preference"

class UnknownPayload(BaseModel):
    fact_key: str
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0

class RecalculatePayload(BaseModel):
    subject_relation: SubjectRelation = "myself"
    member_index: int = 0

class HouseholdMemberRegisterPayload(BaseModel):
    subject_relation: SubjectRelation
    member_index: Optional[int] = None
    display_name: Optional[str] = None
    consent_given: bool = True
    consent_type: str = "representative_declaration"
