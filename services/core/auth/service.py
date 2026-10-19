"""
Optional Account and Saved State Service (Milestone J)
Enforces AUTH_ACCOUNTS_ENABLED=false by default.
Default anonymous citizen discovery session flow operates with ZERO prompts or interruptions.
"""
import os
import time
import uuid
import hashlib
import secrets
from typing import Optional, Dict, Any, List

from .models import (
    CitizenAccount,
    CitizenProfile,
    Bookmark,
    SavedApplication,
    Reminder,
)


class AccountsDisabledError(RuntimeError):
    """Raised when an account action is invoked while optional accounts are disabled."""
    pass


def is_accounts_enabled() -> bool:
    """Returns True if optional citizen accounts are explicitly enabled."""
    return os.getenv("AUTH_ACCOUNTS_ENABLED", "false").strip().lower() in ("true", "1", "yes")


class AccountService:
    def __init__(self):
        # In-memory storage for demonstration and fast testing; connects to DB models when configured
        self._accounts: Dict[str, CitizenAccount] = {}
        self._accounts_by_identifier: Dict[str, str] = {}  # identifier -> account_id
        self._profiles: Dict[str, CitizenProfile] = {}
        self._bookmarks: Dict[str, List[Bookmark]] = {}  # account_id -> list of bookmarks
        self._applications: Dict[str, Dict[str, SavedApplication]] = {}  # account_id -> {app_id: app}
        self._reminders: Dict[str, List[Reminder]] = {}  # account_id -> list of reminders
        self._anonymous_sessions: Dict[str, Dict[str, Any]] = {}

    def _hash_password(self, secret: str, salt: Optional[bytes] = None) -> str:
        if salt is None:
            salt = secrets.token_bytes(16)
        iterations = 100_000
        dk = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, iterations)
        return f"{salt.hex()}:{iterations}:{dk.hex()}"

    def _verify_password(self, secret: str, stored_hash: str) -> bool:
        try:
            salt_hex, iterations_str, hash_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            iterations = int(iterations_str)
            dk = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, iterations)
            return secrets.compare_digest(dk.hex(), hash_hex)
        except Exception:
            return False

    def _ensure_enabled(self) -> None:
        if not is_accounts_enabled():
            raise AccountsDisabledError(
                "Optional citizen accounts feature is currently disabled (AUTH_ACCOUNTS_ENABLED=false). "
                "Citizen discovery flow runs 100% anonymously with no account required."
            )

    # --- Anonymous Citizen Discovery Flow ---
    def get_or_create_anonymous_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Default anonymous session flow. Always works regardless of AUTH_ACCOUNTS_ENABLED.
        Zero interruptions, zero sign-up prompts.
        """
        if session_id and session_id in self._anonymous_sessions:
            return self._anonymous_sessions[session_id]

        new_id = session_id or f"anon_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": new_id,
            "is_anonymous": True,
            "created_at": time.time(),
            "facts": {},
            "temporary_bookmarks": [],
            "history": []
        }
        self._anonymous_sessions[new_id] = session
        return session

    def record_anonymous_fact(self, session_id: str, fact_key: str, value: Any) -> None:
        """Stores a demographic fact within an anonymous session without an account."""
        session = self.get_or_create_anonymous_session(session_id)
        session["facts"][fact_key] = value

    # --- Optional Account Management (Gated behind AUTH_ACCOUNTS_ENABLED) ---
    def create_account(
        self,
        identifier: str,
        password: str,
        initial_facts: Optional[Dict[str, Any]] = None,
        from_session_id: Optional[str] = None
    ) -> CitizenAccount:
        self._ensure_enabled()

        clean_id = identifier.strip().lower()
        if clean_id in self._accounts_by_identifier:
            raise ValueError(f"Account with identifier '{identifier}' already exists.")

        hashed_secret = self._hash_password(password)
        account = CitizenAccount.create(identifier=clean_id, hashed_secret=hashed_secret)

        self._accounts[account.id] = account
        self._accounts_by_identifier[clean_id] = account.id

        # Profile facts
        facts = initial_facts or {}
        # If migrating from an anonymous session
        if from_session_id and from_session_id in self._anonymous_sessions:
            anon = self._anonymous_sessions[from_session_id]
            facts.update(anon.get("facts", {}))
            # migrate bookmarks
            for scheme_id in anon.get("temporary_bookmarks", []):
                self.add_bookmark(account.id, scheme_id, notes="Migrated from anonymous session")

        self._profiles[account.id] = CitizenProfile(account_id=account.id, facts=facts)
        return account

    def authenticate(self, identifier: str, password: str) -> CitizenAccount:
        self._ensure_enabled()

        clean_id = identifier.strip().lower()
        account_id = self._accounts_by_identifier.get(clean_id)
        if not account_id:
            raise ValueError("Invalid identifier or password.")

        account = self._accounts.get(account_id)
        if not account or not account.is_active:
            raise ValueError("Account not found or inactive.")

        if not self._verify_password(password, account.hashed_secret):
            raise ValueError("Invalid identifier or password.")

        return account

    def get_account(self, account_id: str) -> Optional[CitizenAccount]:
        self._ensure_enabled()
        return self._accounts.get(account_id)

    def get_profile(self, account_id: str) -> Optional[CitizenProfile]:
        self._ensure_enabled()
        return self._profiles.get(account_id)

    def update_profile(
        self,
        account_id: str,
        facts: Dict[str, Any],
        household_members: Optional[List[Dict[str, Any]]] = None
    ) -> CitizenProfile:
        self._ensure_enabled()
        profile = self._profiles.get(account_id)
        if not profile:
            profile = CitizenProfile(account_id=account_id)
            self._profiles[account_id] = profile

        profile.facts.update(facts)
        if household_members is not None:
            profile.household_members = household_members
        profile.updated_at = time.time()
        return profile

    # --- Saved State: Bookmarks ---
    def add_bookmark(
        self,
        account_id: str,
        scheme_id: str,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Bookmark:
        self._ensure_enabled()
        if account_id not in self._bookmarks:
            self._bookmarks[account_id] = []

        # Prevent duplicate bookmark
        for b in self._bookmarks[account_id]:
            if b.scheme_id == scheme_id:
                b.notes = notes or b.notes
                if tags:
                    b.tags = tags
                return b

        bookmark = Bookmark.create(account_id=account_id, scheme_id=scheme_id, notes=notes, tags=tags)
        self._bookmarks[account_id].append(bookmark)
        return bookmark

    def get_bookmarks(self, account_id: str) -> List[Bookmark]:
        self._ensure_enabled()
        return list(self._bookmarks.get(account_id, []))

    def remove_bookmark(self, account_id: str, scheme_id: str) -> bool:
        self._ensure_enabled()
        b_list = self._bookmarks.get(account_id, [])
        initial_len = len(b_list)
        self._bookmarks[account_id] = [b for b in b_list if b.scheme_id != scheme_id]
        return len(self._bookmarks[account_id]) < initial_len

    # --- Saved State: Applications ---
    def save_application(
        self,
        account_id: str,
        scheme_id: str,
        status: str = "DRAFT",
        notes: Optional[str] = None,
        deadline: Optional[float] = None,
        tracking_number: Optional[str] = None
    ) -> SavedApplication:
        self._ensure_enabled()
        if account_id not in self._applications:
            self._applications[account_id] = {}

        # check if application for scheme already exists
        for app in self._applications[account_id].values():
            if app.scheme_id == scheme_id:
                app.status = status
                app.notes = notes or app.notes
                app.deadline = deadline or app.deadline
                app.tracking_number = tracking_number or app.tracking_number
                app.updated_at = time.time()
                return app

        app = SavedApplication.create(
            account_id=account_id,
            scheme_id=scheme_id,
            status=status,
            notes=notes,
            deadline=deadline,
            tracking_number=tracking_number
        )
        self._applications[account_id][app.id] = app
        return app

    def get_applications(self, account_id: str) -> List[SavedApplication]:
        self._ensure_enabled()
        return list(self._applications.get(account_id, {}).values())

    def update_application_status(
        self,
        account_id: str,
        application_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> SavedApplication:
        self._ensure_enabled()
        apps = self._applications.get(account_id, {})
        if application_id not in apps:
            raise KeyError(f"Application {application_id} not found.")

        app = apps[application_id]
        app.status = status
        if notes:
            app.notes = notes
        if status == "SUBMITTED" and not app.applied_at:
            app.applied_at = time.time()
        app.updated_at = time.time()
        return app

    # --- Saved State: Reminders ---
    def add_reminder(
        self,
        account_id: str,
        scheme_id: str,
        title: str,
        due_date: float
    ) -> Reminder:
        self._ensure_enabled()
        if account_id not in self._reminders:
            self._reminders[account_id] = []

        reminder = Reminder.create(account_id=account_id, scheme_id=scheme_id, title=title, due_date=due_date)
        self._reminders[account_id].append(reminder)
        return reminder

    def get_reminders(self, account_id: str, include_completed: bool = False) -> List[Reminder]:
        self._ensure_enabled()
        rems = self._reminders.get(account_id, [])
        if include_completed:
            return list(rems)
        return [r for r in rems if not r.is_completed]

    def complete_reminder(self, account_id: str, reminder_id: str) -> bool:
        self._ensure_enabled()
        for r in self._reminders.get(account_id, []):
            if r.id == reminder_id:
                r.is_completed = True
                return True
        return False


# Global singleton instance
account_service = AccountService()
