"""
Role-Based Access Control (RBAC) Module (Milestones K & P)
Implements least-privilege role boundaries for administrative operations.
Roles:
- reviewer: Rule evaluation, conflict resolution, dossier inspection
- publisher: Rule publishing, deprecation, supersession governance
- auditor: Compliance inspection, audit trail verification, telemetry monitoring
- admin: Full administrative governance and configuration
"""
from enum import Enum
from typing import Set, List, Optional, Dict, Any, Union
import logging
import time
from fastapi import HTTPException, Depends, Security

from ..auth.principal import AuthenticatedPrincipal, get_current_principal

logger = logging.getLogger("civixai.security.rbac")


class Role(str, Enum):
    REVIEWER = "reviewer"
    PUBLISHER = "publisher"
    AUDITOR = "auditor"
    ADMIN = "admin"


class Permission(str, Enum):
    VIEW_SCHEMES = "view_schemes"
    REVIEW_RULES = "review_rules"
    RESOLVE_CONFLICTS = "resolve_conflicts"
    VIEW_DOSSIERS = "view_dossiers"
    PUBLISH_SCHEMES = "publish_schemes"
    DEPRECATE_SCHEMES = "deprecate_schemes"
    SUPERSEDE_SCHEMES = "supersede_schemes"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_REPORTS = "export_reports"
    VIEW_TELEMETRY = "view_telemetry"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    PURGE_DATA = "purge_data"
    ADMIN = "*"


ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    Role.REVIEWER.value: {
        Permission.VIEW_SCHEMES.value,
        Permission.REVIEW_RULES.value,
        Permission.RESOLVE_CONFLICTS.value,
        Permission.VIEW_DOSSIERS.value,
    },
    Role.PUBLISHER.value: {
        Permission.VIEW_SCHEMES.value,
        Permission.PUBLISH_SCHEMES.value,
        Permission.DEPRECATE_SCHEMES.value,
        Permission.SUPERSEDE_SCHEMES.value,
    },
    Role.AUDITOR.value: {
        Permission.VIEW_SCHEMES.value,
        Permission.VIEW_AUDIT_LOGS.value,
        Permission.EXPORT_REPORTS.value,
        Permission.VIEW_TELEMETRY.value,
    },
    Role.ADMIN.value: {
        Permission.ADMIN.value,
        Permission.VIEW_SCHEMES.value,
        Permission.REVIEW_RULES.value,
        Permission.RESOLVE_CONFLICTS.value,
        Permission.VIEW_DOSSIERS.value,
        Permission.PUBLISH_SCHEMES.value,
        Permission.DEPRECATE_SCHEMES.value,
        Permission.SUPERSEDE_SCHEMES.value,
        Permission.VIEW_AUDIT_LOGS.value,
        Permission.EXPORT_REPORTS.value,
        Permission.VIEW_TELEMETRY.value,
        Permission.MANAGE_USERS.value,
        Permission.MANAGE_ROLES.value,
        Permission.PURGE_DATA.value,
    },
}


class RBACManager:
    """RBAC security manager providing permission checks and security audit logging."""

    def __init__(self):
        self._audit_logs: List[Dict[str, Any]] = []

    def get_role_permissions(self, role: str) -> Set[str]:
        clean_role = role.strip().lower()
        return set(ROLE_PERMISSIONS.get(clean_role, set()))

    def has_role(self, principal: AuthenticatedPrincipal, allowed_roles: Union[str, List[str], Set[str]]) -> bool:
        if isinstance(allowed_roles, str):
            allowed = {allowed_roles.lower()}
        else:
            allowed = {r.lower() for r in allowed_roles}

        # Admin / Superadmin always possesses access
        if principal.role.lower() in ("admin", "superadmin", Role.ADMIN.value):
            return True

        return principal.role.lower() in allowed

    def has_permission(self, principal: AuthenticatedPrincipal, required_perm: str) -> bool:
        perm_clean = required_perm.strip().lower()

        # Check if principal is admin or has wildcard admin
        if principal.role.lower() in ("admin", "superadmin", Role.ADMIN.value):
            return True
        if "*" in principal.permissions or "admin" in principal.permissions:
            return True

        # Check explicitly attached permissions
        if perm_clean in {p.lower() for p in principal.permissions}:
            return True

        # Check role-inherited permissions
        role_perms = self.get_role_permissions(principal.role)
        return perm_clean in role_perms

    def log_access_event(
        self,
        principal: AuthenticatedPrincipal,
        action: str,
        resource: str,
        granted: bool,
        reason: Optional[str] = None
    ) -> None:
        event = {
            "timestamp": time.time(),
            "actor_id": principal.actor_id,
            "role": principal.role,
            "action": action,
            "resource": resource,
            "granted": granted,
            "reason": reason,
        }
        self._audit_logs.append(event)
        if not granted:
            logger.warning(
                f"RBAC ACCESS DENIED: Actor '{principal.actor_id}' (Role: '{principal.role}') "
                f"denied access to '{action}' on '{resource}'. Reason: {reason}"
            )

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        return list(self._audit_logs)


rbac_manager = RBACManager()


def require_role(*roles: str):
    """
    FastAPI dependency factory enforcing that the authenticated principal has one of the allowed roles.
    """
    allowed = {r.lower() for r in roles}

    def role_checker(principal: AuthenticatedPrincipal = Depends(get_current_principal)) -> AuthenticatedPrincipal:
        if not rbac_manager.has_role(principal, allowed):
            rbac_manager.log_access_event(
                principal=principal,
                action=f"require_role({','.join(roles)})",
                resource="admin_endpoint",
                granted=False,
                reason=f"Principal role '{principal.role}' not in required roles: {roles}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Principal role '{principal.role}' lacks required role privileges: {roles}"
            )

        rbac_manager.log_access_event(
            principal=principal,
            action=f"require_role({','.join(roles)})",
            resource="admin_endpoint",
            granted=True
        )
        return principal

    return role_checker


def require_permission(perm: str):
    """
    FastAPI dependency factory enforcing that the authenticated principal possesses a specific permission.
    """
    def permission_checker(principal: AuthenticatedPrincipal = Depends(get_current_principal)) -> AuthenticatedPrincipal:
        if not rbac_manager.has_permission(principal, perm):
            rbac_manager.log_access_event(
                principal=principal,
                action=f"require_permission({perm})",
                resource="admin_endpoint",
                granted=False,
                reason=f"Principal lacks required permission '{perm}'"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Principal '{principal.actor_id}' lacks required permission: '{perm}'"
            )

        rbac_manager.log_access_event(
            principal=principal,
            action=f"require_permission({perm})",
            resource="admin_endpoint",
            granted=True
        )
        return principal

    return permission_checker
