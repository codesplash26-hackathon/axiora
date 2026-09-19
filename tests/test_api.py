import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True


def test_predict_endpoint_low_risk(client):
    payload = {
        "male": 0,
        "age": 35,
        "currentSmoker": 0,
        "cigsPerDay": 0.0,
        "BPMeds": 0.0,
        "prevalentStroke": 0,
        "prevalentHyp": 0,
        "diabetes": 0,
        "totChol": 160.0,
        "sysBP": 110.0,
        "diaBP": 72.0,
        "BMI": 21.5,
        "heartRate": 65.0,
        "glucose": 80.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_band"] == "Low"
    assert data["requires_recourse"] is False
    assert data["risk_percentage"] == round(data["risk_score"] * 100.0, 2)


def test_predict_endpoint_high_risk(client):
    payload = {
        "male": 1,
        "age": 68,
        "currentSmoker": 1,
        "cigsPerDay": 30.0,
        "BPMeds": 1.0,
        "prevalentStroke": 0,
        "prevalentHyp": 1,
        "diabetes": 1,
        "totChol": 285.0,
        "sysBP": 185.0,
        "diaBP": 105.0,
        "BMI": 33.2,
        "heartRate": 88.0,
        "glucose": 190.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] > 0.15
    assert data["risk_band"] in ["Borderline", "High"]
    assert isinstance(data["requires_recourse"], bool)


def test_predict_endpoint_validation_error(client):
    payload = {
        "male": 1,
        "age": 55,
        "sysBP": 350.0,  # Exceeds physiological upper boundary (295.0)
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_explain_endpoint(client):
    payload = {
        "male": 1,
        "age": 50,
        "currentSmoker": 1,
        "cigsPerDay": 15.0,
        "BPMeds": 0.0,
        "prevalentStroke": 0,
        "prevalentHyp": 0,
        "diabetes": 0,
        "totChol": 210.0,
        "sysBP": 130.0,
        "diaBP": 85.0,
        "BMI": 25.0,
        "heartRate": 72.0,
        "glucose": 85.0,
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "base_value" in data
    assert "attributions" in data


def test_recourse_endpoint(client):
    payload = {
        "male": 1,
        "age": 50,
        "currentSmoker": 1,
        "cigsPerDay": 15.0,
        "BPMeds": 0.0,
        "prevalentStroke": 0,
        "prevalentHyp": 0,
        "diabetes": 0,
        "totChol": 210.0,
        "sysBP": 130.0,
        "diaBP": 85.0,
        "BMI": 25.0,
        "heartRate": 72.0,
        "glucose": 85.0,
    }
    response = client.post("/recourse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "patient_baseline_risk" in data
    assert "pathways" in data
