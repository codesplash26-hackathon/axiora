import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth.auth_handler import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.auth.auth_routes import router as auth_router

app = FastAPI()
app.include_router(auth_router)
client = TestClient(app)


def test_password_hashing_and_verification():
    raw_pw = "DoctorSecret2026!"
    hashed = hash_password(raw_pw)
    assert hashed != raw_pw
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_creation_and_decoding():
    payload = {"sub": "doc_xyz_999", "email": "test@cardiorecourse.lk", "role": "doctor"}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded["sub"] == "doc_xyz_999"
    assert decoded["email"] == "test@cardiorecourse.lk"
    assert decoded["role"] == "doctor"
    assert "exp" in decoded


def test_doctor_registration_and_login_flow():
    email = "dr.kumara@hospital.lk"
    password = "SecurePassword123"

    # 1. Register
    reg_payload = {
        "email": email,
        "password": password,
        "fullName": "Dr. Kumara Jayasinghe",
        "specialization": "Interventional Cardiology",
        "hospital": "Kandy General Hospital",
    }
    resp = client.post("/auth/doctor/register", json=reg_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["doctor"]["email"] == email
    assert data["doctor"]["fullName"] == "Dr. Kumara Jayasinghe"

    # 2. Duplicate registration should fail
    dup_resp = client.post("/auth/doctor/register", json=reg_payload)
    assert dup_resp.status_code == 400

    # 3. Login with correct password
    login_resp = client.post("/auth/doctor/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["access_token"]
    assert token is not None

    # 4. Login with incorrect password
    bad_login = client.post("/auth/doctor/login", json={"email": email, "password": "WrongPassword"})
    assert bad_login.status_code == 401

    # 5. Access /me with valid token
    me_resp = client.get("/auth/doctor/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    # 6. Access /me without token
    unauth_resp = client.get("/auth/doctor/me")
    assert unauth_resp.status_code == 401
