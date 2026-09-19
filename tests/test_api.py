import pytest
from fastapi.testclient import TestClient
from backend.main import app
import config

valid_patient = {
    "male": 1,
    "age": 55.0,
    "currentSmoker": 1,
    "cigsPerDay": 20.0,
    "BPMeds": 0,
    "prevalentStroke": 0,
    "prevalentHyp": 1,
    "diabetes": 0,
    "totChol": 260.0,
    "sysBP": 150.0,
    "diaBP": 95.0,
    "BMI": 28.5,
    "heartRate": 85.0,
    "glucose": 95.0
}

def test_health_check():
    # Lifespan isn't strictly necessary for a simple health check, but good practice
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

def test_explain_endpoint_success():
    with TestClient(app) as client:
        response = client.post("/explain", json=valid_patient)
        assert response.status_code == 200
        
        data = response.json()
        
        assert "base_value" in data
        assert "risk_score" in data
        assert "attributions" in data
        
        assert 0.0 <= data["base_value"] <= 1.0
        assert 0.0 <= data["risk_score"] <= 1.0
        
        attributions = data["attributions"]
        assert isinstance(attributions, list)
        assert len(attributions) > 0
        
        # Verify schema
        for attr in attributions:
            assert "feature" in attr
            assert "display_name" in attr
            assert "attribution_value" in attr
            assert "patient_value" in attr
            assert "direction" in attr
            assert attr["direction"] in ["risk_increasing", "protective"]

def test_explain_endpoint_invalid_data():
    invalid_patient = valid_patient.copy()
    invalid_patient["sysBP"] = "Not a number"
    
    with TestClient(app) as client:
        response = client.post("/explain", json=invalid_patient)
        assert response.status_code == 422
