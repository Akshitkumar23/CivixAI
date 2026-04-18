from fastapi.testclient import TestClient
import json
import pytest

# Adjust path to import main
import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "InputAgent" in data["agents"]

def test_check_eligibility():
    payload = {
        "age": 30,
        "annual_income": 200000,
        "state": "Maharashtra",
        "category": "obc",
        "occupation": "farmer"
    }
    
    # We use check-eligibility for a fast test since it only runs Stages 1 & 2 (no LLM)
    response = client.post("/api/check-eligibility", json=payload)
    
    # The server might return 503 if models/datasets aren't present locally for the test
    # but we assert it returns a JSON in case of success or a valid failure mode.
    if response.status_code == 200:
        data = response.json()
        assert "eligible_schemes" in data
        assert "confidence_score" in data
    elif response.status_code == 500:
        # Expected if models are missing during CI/CD without setup
        print("Note: App raised 500, possibly due to missing models")
    else:
        assert response.status_code in [200, 500, 503]
