from __future__ import annotations
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

class CollectionMethod(str, Enum):
    QUESTION = "QUESTION"
    DETERMINISTIC_DERIVATION = "DETERMINISTIC_DERIVATION"
    USER_DECLARATION = "USER_DECLARATION"
    DOCUMENT_VERIFICATION = "DOCUMENT_VERIFICATION"
    EXTERNAL_VERIFICATION = "EXTERNAL_VERIFICATION"
    SYSTEM_CONTEXT = "SYSTEM_CONTEXT"

class SubjectScope(str, Enum):
    APPLICANT = "applicant"
    BENEFICIARY = "beneficiary"
    HOUSEHOLD = "household"
    FAMILY = "family"
    STUDENT = "student"
    ARTISAN = "artisan"
    ENTERPRISE = "enterprise"
    LOCATION = "location"

class DataType(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    ENUM = "enum"

class VerificationLevel(str, Enum):
    SELF_DECLARED = "self_declared"
    DOCUMENT_SUPPORTED = "document_supported"
    GOVERNMENT_VERIFIED = "government_verified"

class CanonicalFactDefinition(BaseModel):
    fact_key: str
    subject_scope: SubjectScope = SubjectScope.APPLICANT
    data_type: DataType = DataType.STRING
    allowed_values: Optional[List[Any]] = None
    aliases: List[str] = Field(default_factory=list)
    unit: Optional[str] = None
    sensitivity: str = "normal"  # normal, sensitive, financial
    collection_method: CollectionMethod = CollectionMethod.QUESTION
    verification_level: VerificationLevel = VerificationLevel.SELF_DECLARED
    question_available: bool = True
    derivation_policy: Optional[str] = None  # None or registered derivation rule ID
    normalization_policy: str = "standard_trim_casefold"
    schemes_using_fact: List[str] = Field(default_factory=list)
    source_semantics: str = ""

    def validate_value(self, value: Any) -> Any:
        """Type validates and casts the incoming value strictly and deterministically."""
        if value is None:
            return None

        if self.data_type == DataType.INTEGER:
            if isinstance(value, bool):
                raise ValueError(f"Cannot treat boolean {value} as integer for {self.fact_key}")
            return int(value)
        elif self.data_type == DataType.FLOAT:
            if isinstance(value, bool):
                raise ValueError(f"Cannot treat boolean {value} as float for {self.fact_key}")
            return float(value)
        elif self.data_type == DataType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                v_clean = value.strip().lower()
                if v_clean in ("true", "1", "yes"):
                    return True
                elif v_clean in ("false", "0", "no"):
                    return False
                raise ValueError(f"Cannot cast string '{value}' to boolean for {self.fact_key}")
            return bool(value)
        elif self.data_type == DataType.ENUM:
            val_str = str(value).strip().lower()
            if self.allowed_values and val_str not in [str(x).lower() for x in self.allowed_values]:
                raise ValueError(f"Value '{value}' not in allowed values for {self.fact_key}: {self.allowed_values}")
            return val_str
        elif self.data_type == DataType.STRING:
            return str(value).strip()

        return value

