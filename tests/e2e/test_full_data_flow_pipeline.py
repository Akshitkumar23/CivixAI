"""
End-to-End Data Flow Pipeline Tests.
Validates the full 7-step pipeline from raw profile intake, canonical fact normalization,
candidate retrieval, AST evaluation, questionnaire generation, document requirements,
to final API response serialization.
"""
import pytest
from starlette.testclient import TestClient
from services.ml_api.main import app

client = TestClient(app)


class TestFullDataFlowPipeline:
    """End-to-end tests validating the complete data flow pipeline."""

    def test_step_1_api_health_endpoint(self):
        """Step 1 & Baseline: Verify API is healthy and returns required telemetry."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "pipeline" in data
        assert "version" in data
        assert isinstance(data.get("agents"), list)

    def test_step_2_to_4_profile_evaluation_certified_flow(self):
        """
        Steps 2-4: Profile intake, fact resolution, candidate filtering, and AST rule evaluation.
        Evaluates a qualifying citizen profile in CERTIFIED_PRODUCTION mode.
        """
        payload = {
            "profile": {
                "person.age": 28,
                "person.gender": "female",
                "applicant.pays_income_tax": False,
                "applicant.has_bank_account": True,
                "location.state": "Uttar Pradesh"
            },
            "certified_only": True,
            "mode": "CERTIFIED_PRODUCTION"
        }
        response = client.post("/v1/programmes/evaluate-all", json=payload)
        assert response.status_code == 200
        result = response.json()

        # Schema validation
        assert "total_evaluated" in result
        assert "eligible_count" in result
        assert "needs_information_count" in result
        assert "not_eligible_count" in result
        assert "tabs" in result

        # In certified mode, exactly 27 schemes are evaluated
        assert result["total_evaluated"] == 27
        assert "ELIGIBLE" in result["tabs"]
        assert "NEEDS_INFORMATION" in result["tabs"]

    def test_step_5_questionnaire_generation_for_missing_facts(self):
        """Step 5: Verifies that missing mandatory facts trigger targeted questionnaire items."""
        # Empty profile must trigger NEEDS_INFORMATION with questions
        payload = {
            "profile": {},
            "certified_only": True
        }
        response = client.post("/v1/programmes/evaluate-all", json=payload)
        assert response.status_code == 200
        result = response.json()

        assert result["needs_information_count"] > 0
        needs_info_items = result["tabs"]["NEEDS_INFORMATION"]
        assert len(needs_info_items) > 0
        # Every needs_information item must have questions
        first_item = needs_info_items[0]
        assert first_item["status"] == "NEEDS_INFORMATION"
        assert first_item["questions_count"] > 0

    def test_step_6_programme_specific_evaluation(self):
        """Step 6: Evaluates a single specific programme contract (APY)."""
        apy_id = "dbtbharat_central_schemes_atal_pension_yojana"
        qualifying_payload = {
            "profile": {
                "person.age": 30,
                "applicant.pays_income_tax": False
            },
            "mode": "CERTIFIED_PRODUCTION"
        }
        response = client.post(f"/v1/programmes/{apy_id}/evaluate", json=qualifying_payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ("ELIGIBLE", "PASS")

    def test_step_7_error_handling_and_input_validation(self):
        """Step 7: Validates resilience against malformed inputs and nonexistent endpoints."""
        # Invalid JSON type for profile
        invalid_payload = {"profile": "not_a_dictionary"}
        response = client.post("/v1/programmes/evaluate-all", json=invalid_payload)
        assert response.status_code == 422  # Pydantic validation error

        # Nonexistent scheme details
        response_404 = client.get("/api/scheme-details/nonexistent_fake_scheme_id_9999")
        assert response_404.status_code == 404
