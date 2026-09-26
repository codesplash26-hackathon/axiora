import re
from typing import Dict, Any, List, Tuple, Set

# Standard direct identifier keys under HIPAA Safe Harbor (45 CFR § 164.514)
# and Sri Lanka Personal Data Protection Act (PDPA No. 9 of 2022)
PHI_EXCLUDED_KEYS: Set[str] = {
    "name", "first_name", "last_name", "fullname", "full_name", "patient_name",
    "email", "email_address", "mail",
    "phone", "phone_number", "telephone", "mobile", "cell", "contact",
    "ssn", "social_security", "nic", "national_id", "id_number", "passport", "driving_license",
    "address", "street", "city", "state", "zip", "zipcode", "postal_code",
    "mrn", "medical_record_number", "patient_id", "pid", "id",
    "dob", "birth_date", "date_of_birth", "birthday",
    "ip", "ip_address", "mac", "mac_address", "device_id",
    "hospital", "clinic", "doctor", "physician", "notes", "comments"
}

# Network-level HTTP headers carrying client identity or network topology
NETWORK_IDENTIFIER_HEADERS: Set[bytes] = {
    b"x-forwarded-for",
    b"user-agent",
    b"referer",
    b"x-real-ip",
    b"cf-connecting-ip",
    b"forwarded",
    b"via",
    b"client-ip",
    b"true-client-ip",
    b"x-cluster-client-ip"
}

# Regex patterns matching direct text identifiers in payload values
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}")
NIC_SRI_LANKA_REGEX = re.compile(r"\b\d{9}[vVxX]\b|\b\d{12}\b")
SSN_US_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def is_phi_key(key: str) -> bool:
    """Check if key name matches known direct health or personal identifier patterns."""
    k_norm = key.strip().lower()
    if k_norm in PHI_EXCLUDED_KEYS:
        return True
    for excluded in PHI_EXCLUDED_KEYS:
        if excluded in k_norm and len(excluded) > 2:
            return True
    return False


def contains_phi_value(value: Any) -> bool:
    """Scan arbitrary values for direct identifiers like emails, phones, or ID numbers."""
    if not isinstance(value, str):
        return False
    val_str = value.strip()
    if EMAIL_REGEX.search(val_str):
        return True
    if PHONE_REGEX.search(val_str) and sum(c.isdigit() for c in val_str) >= 7:
        return True
    if NIC_SRI_LANKA_REGEX.search(val_str):
        return True
    if SSN_US_REGEX.search(val_str):
        return True
    return False


def _sanitize_list(items: List[Any], parent_key: str) -> Tuple[List[Any], List[str]]:
    """Recursively inspect and purge PHI values or sub-dictionaries from arrays."""
    clean_items = []
    purged = []
    for idx, item in enumerate(items):
        item_path = f"{parent_key}[{idx}]"
        if contains_phi_value(item):
            purged.append(item_path)
            continue
        if isinstance(item, dict):
            sub_clean, sub_purged = sanitize_patient_payload(item)
            clean_items.append(sub_clean)
            purged.extend([f"{item_path}.{sk}" for sk in sub_purged])
        elif isinstance(item, list):
            sub_clean, sub_purged = _sanitize_list(item, item_path)
            clean_items.append(sub_clean)
            purged.extend(sub_purged)
        else:
            clean_items.append(item)
    return clean_items, purged


def sanitize_patient_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Purge all direct text identifiers and PHI metadata from incoming payload.
    Returns:
        (sanitized_dict, list_of_purged_keys)
    """
    if not isinstance(payload, dict):
        return payload, []

    sanitized = {}
    purged_keys = []

    for k, v in payload.items():
        if is_phi_key(k):
            purged_keys.append(k)
            continue

        if contains_phi_value(v):
            purged_keys.append(k)
            continue

        # If nested dictionary, sanitize recursively
        if isinstance(v, dict):
            sub_sanitized, sub_purged = sanitize_patient_payload(v)
            sanitized[k] = sub_sanitized
            purged_keys.extend([f"{k}.{sk}" for sk in sub_purged])
        elif isinstance(v, list):
            clean_list, sub_purged = _sanitize_list(v, k)
            sanitized[k] = clean_list
            purged_keys.extend(sub_purged)
        else:
            sanitized[k] = v

    return sanitized, purged_keys

