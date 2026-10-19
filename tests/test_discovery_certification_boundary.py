"""
Sovereign Discovery vs. Certification Boundary Invariant Tests.
Verifies that:
1. Production certified recommendations strictly evaluate the 27 certified reference schemes.
2. CandidateService enforces citizen-only audience filtering (excluding institutional/NGO grants).
3. CandidateService with certified_only=True returns exactly the certified schemes.
4. Production eligibility engine respects certified_only boundary.
"""
import pytest
from services.core.database.session import SessionLocal
from services.core.recommendations.candidate_service import CandidateService
from services.core.eligibility.production_grade_evaluator import production_eligibility_engine


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


class TestDiscoveryCertificationBoundary:
    """Verifies strict boundary between broad discovery catalogue and certified production pool."""

    def test_certified_pool_contains_exact_27_schemes(self, db_session):
        cs = CandidateService(db_session)
        certified_candidates = cs.get_candidates(certified_only=True)
        # Exactly 27 certified reference schemes
        assert len(certified_candidates) == 27
        for c in certified_candidates:
            assert c.get("scheme_id") or c.get("id")

    def test_all_candidates_exceeds_certified_pool(self, db_session):
        cs = CandidateService(db_session)
        all_candidates = cs.get_candidates(certified_only=False)
        certified_candidates = cs.get_candidates(certified_only=True)
        assert len(all_candidates) > len(certified_candidates)
        assert len(all_candidates) >= 130

    def test_citizen_only_filtering_excludes_institutional_grants(self, db_session):
        cs = CandidateService(db_session)
        citizen_candidates = cs.get_candidates(citizen_only=True, certified_only=False)
        all_candidates = cs.get_candidates(citizen_only=False, certified_only=False)

        # Citizen-only should exclude non-citizen audiences (institutional, NGO, etc.)
        assert len(citizen_candidates) <= len(all_candidates)
        for c in citizen_candidates:
            assert c.get("audience_type") not in ["INSTITUTIONAL_GRANT", "NGO_GRANT", "STATE_OR_LOCAL_BODY_GRANT"]

    def test_production_evaluator_certified_only_mode(self):
        sample_profile = {
            "person.age": 35,
            "person.gender": "male",
            "applicant.is_farmer_family": True,
            "applicant.owns_cultivable_land": True,
            "household.annual_income": 90000,
            "location.state": "Maharashtra"
        }

        # Certified-only evaluation
        cert_eval = production_eligibility_engine.evaluate_all(sample_profile, certified_only=True)
        assert cert_eval["total_evaluated"] == 27
        assert cert_eval["total_evaluated"] < 5742

        # Full catalogue evaluation
        full_eval = production_eligibility_engine.evaluate_all(sample_profile, certified_only=False)
        assert full_eval["total_evaluated"] == 5742
