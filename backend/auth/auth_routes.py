from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from fastapi.security import HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool
from backend.auth.auth_handler import (
    create_access_token,
    decode_access_token,
    get_current_doctor,
    hash_password,
    revoke_token,
    security,
    verify_password,
)
from backend.db.firestore_service import (
    create_doctor,
    get_doctor_by_email,
)

router = APIRouter(prefix="/auth/doctor", tags=["Doctor Authentication"])


class DoctorRegisterRequest(BaseModel):
    email: str = Field(..., description="Doctor's institutional or professional email")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    fullName: str = Field(..., min_length=2, description="Full Name with title (e.g. Dr. Jane Smith)")
    specialization: Optional[str] = Field("Cardiology / General Practice", description="Clinical specialty")
    hospital: Optional[str] = Field("Axiora Health Network", description="Hospital / Clinical Affiliation")


class DoctorLoginRequest(BaseModel):
    email: str = Field(..., description="Doctor's registered email")
    password: str = Field(..., description="Password")


class DoctorProfileResponse(BaseModel):
    doctorId: str
    email: str
    fullName: str
    specialization: str
    hospital: str
    createdAt: str


class DoctorAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    doctor: DoctorProfileResponse


def _clean_doctor_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Removes sensitive password hash before returning doctor profile."""
    safe = dict(doc)
    safe.pop("passwordHash", None)
    return safe


@router.post("/register", response_model=DoctorAuthResponse, status_code=status.HTTP_201_CREATED)
async def register_doctor(payload: DoctorRegisterRequest):
    """
    Registers a new clinician account.
    Stores de-identified doctor credentials in Firestore with bcrypt hashing.
    """
    existing = await run_in_threadpool(get_doctor_by_email, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered.",
        )

    pw_hash = await run_in_threadpool(hash_password, payload.password)
    doctor_record = await run_in_threadpool(
        create_doctor,
        {
            "email": payload.email,
            "fullName": payload.fullName,
            "specialization": payload.specialization,
            "hospital": payload.hospital,
            "passwordHash": pw_hash,
        }
    )

    token = create_access_token({
        "sub": doctor_record["doctorId"],
        "email": doctor_record["email"],
        "role": "doctor",
    })

    return DoctorAuthResponse(
        access_token=token,
        token_type="bearer",
        doctor=DoctorProfileResponse(**_clean_doctor_dict(doctor_record)),
    )


@router.post("/login", response_model=DoctorAuthResponse)
async def login_doctor(payload: DoctorLoginRequest):
    """
    Authenticates a clinician and issues a 24-hour signed JWT access token.
    """
    doctor = await run_in_threadpool(get_doctor_by_email, payload.email)
    password_valid = False
    if doctor:
        password_valid = await run_in_threadpool(
            verify_password, payload.password, doctor.get("passwordHash", "")
        )

    if not doctor or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({
        "sub": doctor["doctorId"],
        "email": doctor["email"],
        "role": "doctor",
    })

    return DoctorAuthResponse(
        access_token=token,
        token_type="bearer",
        doctor=DoctorProfileResponse(**_clean_doctor_dict(doctor)),
    )


@router.get("/me", response_model=DoctorProfileResponse)
async def get_current_doctor_profile(
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """
    Returns the currently authenticated doctor's profile.
    """
    return DoctorProfileResponse(**_clean_doctor_dict(current_doctor))


@router.post("/logout")
async def logout_doctor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    Revokes the current doctor's access token, preventing any further use.
    """
    if credentials and credentials.credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            jti = payload.get("jti")
            if jti:
                revoke_token(jti)
        except Exception:
            pass
    return {"status": "success", "message": "Successfully logged out. Session revoked."}

