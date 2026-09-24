import pytest
from fastapi.testclient import TestClient
from backend.main import app
import config

SAMPLE_PATIENT = {
    "male": 1,
    "age": 55.0,
    "currentSmoker": 1,
    "cigsPerDay": 20.0,
    "BPMeds": 0.0,
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


def test_health_endpoint():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "online"


def test_predict_endpoint():
    with TestClient(app) as client:
        res = client.post("/predict", json=SAMPLE_PATIENT)
        assert res.status_code == 200
        data = res.json()
        assert "risk_score" in data
        assert "risk_band" in data
        assert "requires_recourse" in data
        assert 0.0 <= data["risk_score"] <= 1.0


def test_explain_endpoint():
    with TestClient(app) as client:
        res = client.post("/explain", json=SAMPLE_PATIENT)
        assert res.status_code == 200
        data = res.json()
        assert "base_value" in data
        assert "risk_score" in data
        assert "attributions" in data
        assert len(data["attributions"]) > 0
        assert data["attributions"][0]["direction"] in ["risk_increasing", "protective"]


def test_recourse_endpoint():
    with TestClient(app) as client:
        res = client.post("/recourse", json=SAMPLE_PATIENT)
        assert res.status_code == 200
        data = res.json()
        assert "patient_baseline_risk" in data
        assert len(data["pathways"]) >= 2
        assert "changes" in data["pathways"][0]
        assert len(data["pathways"][0]["changes"]) > 0


def test_explain_endpoint_invalid_data():
    invalid_patient = SAMPLE_PATIENT.copy()
    invalid_patient["sysBP"] = "Not a number"
    with TestClient(app) as client:
        res = client.post("/explain", json=invalid_patient)
        assert res.status_code == 422


def test_assess_composite_endpoint():
    with TestClient(app) as client:
        res = client.post("/assess", json=SAMPLE_PATIENT)
        assert res.status_code == 200
        data = res.json()
        assert "prediction" in data
        assert "explanation" in data
        assert "recourse" in data
        assert "total_latency_ms" in data
        assert data["total_latency_ms"] < 1400.0
        assert 0.0 <= data["prediction"]["risk_score"] <= 1.0
        assert len(data["explanation"]["attributions"]) > 0
        assert len(data["recourse"]["pathways"]) >= 2
