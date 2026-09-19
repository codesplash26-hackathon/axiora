from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

SAMPLE_PATIENT = {
    "male": 1,
    "age": 55,
    "currentSmoker": 1,
    "cigsPerDay": 20.0,
    "BPMeds": 0.0,
    "prevalentStroke": 0,
    "prevalentHyp": 1,
    "diabetes": 0,
    "totChol": 260.0,
    "sysBP": 160.0,
    "diaBP": 95.0,
    "BMI": 28.5,
    "heartRate": 78.0,
    "glucose": 92.0
}

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

def test_predict_endpoint():
    res = client.post("/predict", json=SAMPLE_PATIENT)
    assert res.status_code == 200
    data = res.json()
    assert "risk_score" in data
    assert data["risk_band"] == "High"
    assert data["requires_recourse"] is True

def test_explain_endpoint():
    res = client.post("/explain", json=SAMPLE_PATIENT)
    assert res.status_code == 200
    data = res.json()
    assert "base_value" in data
    assert "attributions" in data
    assert len(data["attributions"]) > 0
    assert data["attributions"][0]["direction"] in ["risk_increasing", "protective"]

def test_recourse_endpoint():
    res = client.post("/recourse", json=SAMPLE_PATIENT)
    assert res.status_code == 200
    data = res.json()
    assert "patient_baseline_risk" in data
    assert len(data["pathways"]) >= 2
    assert "changes" in data["pathways"][0]
    assert len(data["pathways"][0]["changes"]) > 0
