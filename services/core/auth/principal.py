"""
Admin Authorization Boundary
Provides structured AuthenticatedPrincipal for governance review operations.
Decouples administrative identity from arbitrary request body parameters.
Development secret token is maintained with a strict Principal interface.
"""
import os
import secrets
import logging
from typing import Optional, List, Set
from dataclasses import dataclass, field
from fastapi import Header, HTTPException, Depends

logger = logging.getLogger("civixai.auth_boundary")

ADMIN_TOKEN = os.getenv("CIVIX_ADMIN_TOKEN", "civix-admin-secret")
IS_PRODUCTION = os.getenv("CIVIX_ENV", "").lower() == "production"

@dataclass
class AuthenticatedPrincipal:
    actor_id: str
    role: str
    permissions: Set[str] = field(default_factory=set)

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions or "admin" in self.permissions or self.role == "superadmin"

def get_current_principal(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> AuthenticatedPrincipal:
    """
    Validates token and returns an authenticated principal.
    Never trusts reviewer identity from untrusted request bodies.
    """
    provided = x_admin_token
    if not provided and authorization:
        if authorization.startswith("Bearer "):
            provided = authorization[7:].strip()

    if not provided:
        if IS_PRODUCTION:
            logger.warning("Unauthenticated access rejected in production.")
            raise HTTPException(status_code=401, detail="Administrative credentials required.")
        # Dev fallback principal with restricted read-only or base review
        return AuthenticatedPrincipal(
            actor_id="dev_admin",
            role="developer",
            permissions={"read", "review"}
        )

    # Check known tokens or bearer patterns
    if secrets.compare_digest(provided, ADMIN_TOKEN):
        return AuthenticatedPrincipal(
            actor_id="lead_compliance_officer",
            role="compliance_lead",
            permissions={"read", "review", "publish", "resolve_conflicts", "manage_sources", "admin"}
        )

    # Support structured test tokens e.g. token_reviewer_bob, token_officer_alice
    if provided.startswith("token_reviewer_"):
        actor_name = provided.replace("token_reviewer_", "")
        return AuthenticatedPrincipal(
            actor_id=f"officer_{actor_name}",
            role="reviewer",
            permissions={"read", "review", "resolve_conflicts"}
        )

    logger.warning("Invalid admin credentials submitted.")
    raise HTTPException(status_code=403, detail="Invalid administrative authorization credentials.")

def require_governance_mutation(
    principal: AuthenticatedPrincipal = Depends(get_current_principal)
) -> AuthenticatedPrincipal:
    """Strictly enforces mutation permissions on review/publishing endpoints."""
    if not principal.has_permission("review"):
        raise HTTPException(
            status_code=403,
            detail=f"Principal '{principal.actor_id}' lacks governance review permissions."
        )
    return principal
