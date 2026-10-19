"""
Claim-Evidence, Statutory Source Provenance, and Audit Logger Tests.
Tests statutory evidence level classification (Levels A-G), domain conflict detection,
and RBAC audit logger integrity.
"""
import pytest
from services.core.certification.certification_engine import (
    classify_official_source_level,
    check_source_conflict
)
from services.core.security.rbac import (
    RBACManager,
    Role,
    Permission,
    ROLE_PERMISSIONS
)
from services.core.auth.principal import AuthenticatedPrincipal


class TestSourceClassification:
    """Verifies statutory source classification rules across sovereign tiers."""

    def test_classify_central_ministry_level_a(self):
        url = "https://agricoop.nic.in/en/programme/pmkisan"
        assert classify_official_source_level(url) == "LEVEL_A_MINISTRY"

        url2 = "https://tribal.nic.in/schemes.aspx"
        assert classify_official_source_level(url2) == "LEVEL_A_MINISTRY"

    def test_classify_guideline_pdf_level_b(self):
        url = "https://rural.nic.in/sites/default/files/pmayg_guidelines_2024.pdf"
        assert classify_official_source_level(url) == "LEVEL_B_GUIDELINES"

    def test_classify_gazette_level_c(self):
        url = "https://egazette.gov.in/WriteReadData/2023/245678.pdf"
        assert classify_official_source_level(url) == "LEVEL_C_GAZETTE"

    def test_classify_myscheme_portal_level_d(self):
        url = "https://www.myscheme.gov.in/schemes/pm-kisan"
        assert classify_official_source_level(url) == "LEVEL_D_MYSCHEME"

    def test_classify_state_portal_level_e(self):
        url = "https://kerala.gov.in/services/social-security-pension"
        assert classify_official_source_level(url) == "LEVEL_E_STATE_PORTAL"

    def test_classify_service_delivery_level_f(self):
        url = "https://sbi.co.in/portal/schemes"
        assert classify_official_source_level(url) == "LEVEL_F_SERVICE_PORTAL"

    def test_classify_fallback_level_g(self):
        assert classify_official_source_level(None) == "LEVEL_G_OTHER_GOV"
        assert classify_official_source_level("") == "LEVEL_G_OTHER_GOV"
        assert classify_official_source_level("https://unrecognized-external.org/data") == "LEVEL_G_OTHER_GOV"


class TestSourceConflictDetection:
    """Verifies detection of domain conflicts across statutory sources."""

    def test_single_source_verified(self):
        sources = [{"url": "https://pmkisan.gov.in", "publisher": "MoA&FW"}]
        status, conflict = check_source_conflict(sources)
        assert status == "SINGLE_SOURCE_VERIFIED"
        assert conflict is None

    def test_matching_domain_sources(self):
        sources = [
            {"url": "https://pmkisan.gov.in/about", "publisher": "MoA&FW"},
            {"url": "https://pmkisan.gov.in/faq", "publisher": "MoA&FW"}
        ]
        status, conflict = check_source_conflict(sources)
        assert status == "NO_CONFLICT"
        assert conflict is None

    def test_multi_domain_sources_evidence_consistent(self):
        sources = [
            {"url": "https://central-ministry.gov.in/guidelines", "publisher": "Central Ministry"},
            {"url": "https://state-dept.gov.in/circular", "publisher": "State Dept"}
        ]
        status, conflict = check_source_conflict(sources)
        assert status == "EVIDENCE_CONSISTENT"
        assert conflict is None


class TestRBACSecurityAndAuditLogger:
    """Verifies RBAC access control policies and event audit logging."""

    @pytest.fixture
    def rbac(self):
        return RBACManager()

    def test_role_permissions_least_privilege(self, rbac):
        reviewer_perms = rbac.get_role_permissions(Role.REVIEWER.value)
        assert Permission.REVIEW_RULES.value in reviewer_perms
        assert Permission.PURGE_DATA.value not in reviewer_perms
        assert Permission.PUBLISH_SCHEMES.value not in reviewer_perms

        publisher_perms = rbac.get_role_permissions(Role.PUBLISHER.value)
        assert Permission.PUBLISH_SCHEMES.value in publisher_perms
        assert Permission.REVIEW_RULES.value not in publisher_perms

        auditor_perms = rbac.get_role_permissions(Role.AUDITOR.value)
        assert Permission.VIEW_AUDIT_LOGS.value in auditor_perms
        assert Permission.PUBLISH_SCHEMES.value not in auditor_perms

    def test_admin_has_all_privileges(self, rbac):
        admin = AuthenticatedPrincipal(actor_id="admin-1", role="admin", permissions=["*"])
        assert rbac.has_permission(admin, Permission.PURGE_DATA.value)
        assert rbac.has_permission(admin, "any_custom_permission")

    def test_audit_logging_granted_and_denied_events(self, rbac):
        user = AuthenticatedPrincipal(actor_id="reviewer-42", role="reviewer", permissions=[])

        # Test granted access event
        rbac.log_access_event(
            principal=user,
            action="review_rule",
            resource="scheme_pm_kisan",
            granted=True
        )

        # Test denied access event
        rbac.log_access_event(
            principal=user,
            action="purge_data",
            resource="database_tables",
            granted=False,
            reason="Insufficient role privileges for purge operation"
        )

        logs = rbac.get_audit_logs()
        assert len(logs) == 2

        granted_event = logs[0]
        assert granted_event["actor_id"] == "reviewer-42"
        assert granted_event["action"] == "review_rule"
        assert granted_event["granted"] is True

        denied_event = logs[1]
        assert denied_event["actor_id"] == "reviewer-42"
        assert denied_event["action"] == "purge_data"
        assert denied_event["granted"] is False
        assert "Insufficient role privileges" in denied_event["reason"]
