"""
Edge De-Identification & Stateless Ingestion Middleware (Task B7)
Root-level gateway re-exporting privacy protection filters and zero-disk assertion utilities.
"""
from backend.privacy_middleware import PrivacySanitizationMiddleware
from backend.privacy_rules import (
    sanitize_patient_payload,
    is_phi_key,
    contains_phi_value,
    PHI_EXCLUDED_KEYS,
    NETWORK_IDENTIFIER_HEADERS
)
from backend.zero_disk_audit import (
    assert_zero_disk_writes,
    verify_zero_disk_execution
)

__all__ = [
    "PrivacySanitizationMiddleware",
    "sanitize_patient_payload",
    "is_phi_key",
    "contains_phi_value",
    "PHI_EXCLUDED_KEYS",
    "NETWORK_IDENTIFIER_HEADERS",
    "assert_zero_disk_writes",
    "verify_zero_disk_execution"
]
