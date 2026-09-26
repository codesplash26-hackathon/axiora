import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool
from backend.db.firestore_service import get_doctor_by_id

import uuid
import logging

logger = logging.getLogger("cardiorecourse.auth")

_DEFAULT_SECRET = "axiora-cardiorecourse-jwt-clinical-secret-2026"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEFAULT_SECRET)
ENV = os.getenv("ENVIRONMENT", "development").lower()

if ENV in ("production", "prod") and (not os.getenv("JWT_SECRET_KEY") or SECRET_KEY == _DEFAULT_SECRET):
    raise RuntimeError("CRITICAL SECURITY ERROR: Production deployment requires a secure, non-default JWT_SECRET_KEY environment variable.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # Default 24 hours

security = HTTPBearer(auto_error=False)

# In-memory revocation cache for blacklisting tokens upon logout
_REVOKED_TOKENS = set()


def revoke_token(jti: str) -> None:
    """Blacklists a token JTI upon explicit logout."""
    if jti:
        _REVOKED_TOKENS.add(jti)


def is_token_revoked(jti: str) -> bool:
    """Checks whether token JTI has been revoked."""
    if not jti:
        return False
    return jti in _REVOKED_TOKENS


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token with a unique JTI."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token, enforcing revocation checks."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )



async def get_current_doctor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces doctor authentication.
    Extracts Bearer token, validates signature/expiry, and retrieves doctor profile.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    doctor_id = payload.get("sub")
    if not doctor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing doctor identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    doctor = await run_in_threadpool(get_doctor_by_id, doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Doctor account not found or has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return doctor
