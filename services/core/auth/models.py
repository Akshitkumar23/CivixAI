"""
Optional Account and Saved State Models (Milestone J)
Supports citizen accounts, profiles, bookmarks, saved applications, and reminders.
Strictly decoupled from anonymous citizen discovery sessions.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import time
import uuid


@dataclass
class CitizenAccount:
    id: str
    identifier: str  # Phone number or email
    hashed_secret: str
    created_at: float = field(default_factory=time.time)
    is_active: bool = True
    is_anonymous: bool = False

    @classmethod
    def create(cls, identifier: str, hashed_secret: str) -> "CitizenAccount":
        return cls(
            id=str(uuid.uuid4()),
            identifier=identifier,
            hashed_secret=hashed_secret,
            created_at=time.time(),
            is_active=True,
            is_anonymous=False,
        )


@dataclass
class CitizenProfile:
    account_id: str
    facts: Dict[str, Any] = field(default_factory=dict)
    household_members: List[Dict[str, Any]] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)


@dataclass
class Bookmark:
    id: str
    account_id: str
    scheme_id: str
    created_at: float = field(default_factory=time.time)
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @classmethod
    def create(cls, account_id: str, scheme_id: str, notes: Optional[str] = None, tags: Optional[List[str]] = None) -> "Bookmark":
        return cls(
            id=str(uuid.uuid4()),
            account_id=account_id,
            scheme_id=scheme_id,
            created_at=time.time(),
            notes=notes,
            tags=tags or [],
        )


@dataclass
class SavedApplication:
    id: str
    account_id: str
    scheme_id: str
    status: str = "DRAFT"  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED
    applied_at: Optional[float] = None
    deadline: Optional[float] = None
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    updated_at: float = field(default_factory=time.time)

    @classmethod
    def create(
        cls,
        account_id: str,
        scheme_id: str,
        status: str = "DRAFT",
        notes: Optional[str] = None,
        deadline: Optional[float] = None,
        tracking_number: Optional[str] = None,
    ) -> "SavedApplication":
        return cls(
            id=str(uuid.uuid4()),
            account_id=account_id,
            scheme_id=scheme_id,
            status=status,
            applied_at=time.time() if status == "SUBMITTED" else None,
            deadline=deadline,
            notes=notes,
            tracking_number=tracking_number,
            updated_at=time.time(),
        )


@dataclass
class Reminder:
    id: str
    account_id: str
    scheme_id: str
    title: str
    due_date: float
    is_completed: bool = False
    created_at: float = field(default_factory=time.time)

    @classmethod
    def create(cls, account_id: str, scheme_id: str, title: str, due_date: float) -> "Reminder":
        return cls(
            id=str(uuid.uuid4()),
            account_id=account_id,
            scheme_id=scheme_id,
            title=title,
            due_date=due_date,
            is_completed=False,
            created_at=time.time(),
        )
