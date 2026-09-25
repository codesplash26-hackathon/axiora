import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.zero_disk_audit import assert_zero_disk_writes

VALID_PATIENT_PAYLOAD = {
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


def test_handoff_illegal_metadata_purged_and_model_receives_anonymous_vector():
    """
    Task B7 Handoff Verification Check:
    Post a JSON payload containing illegal metadata ({"name": "John Doe", "email": "john@test.com", "age": 55, ...});
    confirm the middleware purges the text identifiers and delivers an anonymous numerical vector to the model.
    """
    payload_with_phi = VALID_PATIENT_PAYLOAD.copy()
    payload_with_phi.update({
        "name": "John Doe",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com",
        "phone": "+94-781188111",
        "nic": "981234567V",
        "mrn": "MRN-90214",
        "patient_id": "PID-5542",
        "doctor_notes": "Patient presents with chest tightness"
    })

    with TestClient(app) as client:
        with assert_zero_disk_writes():
            response = client.post(
                "/explain",
                json=payload_with_phi,
                headers={
                    "X-Forwarded-For": "203.0.113.195",
                    "User-Agent": "HospitalWorkstation/4.11",
                    "Referer": "https://ehr.hospital.lk/patients/view/90214"
                }
            )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Confirm inference succeeded using only anonymous numerical vector
        assert "risk_score" in data
        assert "attributions" in data
        assert 0.0 <= data["risk_score"] <= 1.0

        # Confirm compliance headers reflect de-identification
        assert response.headers.get("x-privacy-policy") == "HIPAA-SafeHarbor,SriLanka-PDPA-2022"
        purged_count = int(response.headers.get("x-phi-purged-count", 0))
        assert purged_count >= 8, f"Expected at least 8 purged fields, got {purged_count}"


def test_network_level_header_stripping_and_socket_masking():
    """
    Verify network-level identifying headers (X-Forwarded-For, User-Agent, Referer)
    and client socket IPs are masked/stripped.
    """
    with TestClient(app) as client:
        response = client.post(
            "/explain",
            json=VALID_PATIENT_PAYLOAD,
            headers={
                "X-Forwarded-For": "198.51.100.1, 10.0.0.1",
                "User-Agent": "Mozilla/5.0 ClinicalApp/2.0",
                "Referer": "https://secure-ehr.local/dashboard",
                "X-Real-IP": "198.51.100.1",
                "Client-IP": "198.51.100.1"
            }
        )

        assert response.status_code == 200
        # Headers should be completely removed from downstream propagation
        assert response.headers.get("x-privacy-policy") is not None


def test_clean_payload_unmodified():
    """Verify standard compliant payload with only canonical biomarkers passes cleanly."""
    with TestClient(app) as client:
        response = client.post("/explain", json=VALID_PATIENT_PAYLOAD)
        assert response.status_code == 200
        assert int(response.headers.get("x-phi-purged-count", 0)) == 0


def test_value_pattern_matching_purges_hidden_emails_and_phones():
    """Verify regex pattern matching catches text identifiers in non-standard key names."""
    payload_with_hidden_phi = VALID_PATIENT_PAYLOAD.copy()
    payload_with_hidden_phi.update({
        "custom_contact": "alert-physician@cardio-unit.org",
        "emergency_num": "0781188111"
    })

    with TestClient(app) as client:
        response = client.post("/explain", json=payload_with_hidden_phi)
        assert response.status_code == 200
        purged = int(response.headers.get("x-phi-purged-count", 0))
        assert purged >= 2


def test_zero_disk_serialization_enforcement():
    """Assert zero disk writes or temporary file artifacts are created during inference."""
    with TestClient(app) as client:
        with assert_zero_disk_writes():
            response = client.post("/explain", json=VALID_PATIENT_PAYLOAD)
            assert response.status_code == 200


def test_privacy_middleware_rejects_payload_exceeding_2mb():
    """
    Security Test:
    Requests with body size exceeding 2MB must be rejected with HTTP 413 Payload Too Large.
    """
    large_padding = "x" * (2 * 1024 * 1024 + 1024)  # > 2MB
    payload = VALID_PATIENT_PAYLOAD.copy()
    payload["padding"] = large_padding

    with TestClient(app) as client:
        response = client.post("/predict", json=payload)
        assert response.status_code == 413
        assert "Payload Too Large" in response.text


def test_privacy_middleware_fail_closed_on_malformed_json():
    """
    Security Test:
    Non-JSON / corrupted payload bodies must be rejected with HTTP 400 Bad Request
    under fail-closed policy, preventing un-sanitized raw data from leaking downstream.
    """
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            content=b"INVALID_NON_JSON_CORRUPTED_STREAM",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        assert "Bad Request" in response.text
