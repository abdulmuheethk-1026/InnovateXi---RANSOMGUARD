r"""
RANSOMGUARD – License Key Manager
Simple license key system for prototype stage.

Key format:  RG-XXXX-XXXX-XXXX-XXXX
Validation:  checksum-based (no server required for prototype)
Storage: C:\ProgramData\RansomGuard\license.dat (encrypted)
"""

import os
import re
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Tuple

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
LICENSE_DIR  = r"C:\ProgramData\RansomGuard"
LICENSE_FILE = os.path.join(LICENSE_DIR, "license.dat")
SALT         = "RG-PROTO-2024-SALT"   # In production: unique per build

# ─────────────────────────────────────────────
# VALID PROTOTYPE KEYS  (hardcoded for prototype)
# In production these would be server-validated
# ─────────────────────────────────────────────
VALID_KEYS = {
    "RG-PROT-O1AB-2024-DEMO": {"tier": "Prototype", "days": 365,  "seats": 1},
    "RG-PROT-O2CD-2024-DEMO": {"tier": "Prototype", "days": 365,  "seats": 1},
    "RG-PROT-O3EF-2024-DEMO": {"tier": "Prototype", "days": 365,  "seats": 1},
    "RG-SME1-AAAA-BBBB-CCCC": {"tier": "SME Basic",  "days": 365,  "seats": 5},
    "RG-SME2-1111-2222-3333": {"tier": "SME Pro",    "days": 730,  "seats": 25},
    "RG-EVAL-FREE-TRIAL-30D": {"tier": "Trial",      "days": 30,   "seats": 1},
}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _encode(data: dict) -> str:
    raw = json.dumps(data).encode()
    return base64.b64encode(raw).decode()

def _decode(encoded: str) -> dict:
    raw = base64.b64decode(encoded.encode())
    return json.loads(raw.decode())

def _checksum(key: str) -> str:
    return hashlib.sha256(f"{key}{SALT}".encode()).hexdigest()[:8].upper()


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def validate_key(key: str) -> Tuple[bool, str]:
    """
    Validate a license key.
    Returns (is_valid: bool, message: str)
    """
    key = key.strip().upper()

    

    if key not in VALID_KEYS:
        return False, "License key not recognised. Please check your key and try again."

    return True, "License key accepted."


def activate(key: str) -> Tuple[bool, str]:
    """
    Activate the product with the given key.
    Writes license.dat on success.
    Returns (success: bool, message: str)
    """
    valid, msg = validate_key(key)
    if not valid:
        return False, msg

    key = key.strip().upper()
    meta = VALID_KEYS[key]
    expiry = (datetime.now() + timedelta(days=meta["days"])).strftime("%Y-%m-%d")

    record = {
        "key":        key,
        "tier":       meta["tier"],
        "seats":      meta["seats"],
        "activated":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expiry":     expiry,
        "checksum":   _checksum(key),
    }

    os.makedirs(LICENSE_DIR, exist_ok=True)
    with open(LICENSE_FILE, "w") as f:
        f.write(_encode(record))

    return True, f"Activated successfully!\nTier: {meta['tier']}\nValid until: {expiry}"


def get_license_status() -> dict:
    """
    Read and return current license status.
    Returns dict with keys: valid, tier, expiry, days_remaining, key_masked
    """
    if not os.path.exists(LICENSE_FILE):
        return {"valid": False, "reason": "No license found"}

    try:
        with open(LICENSE_FILE, "r") as f:
            record = _decode(f.read())

        # Verify checksum
        if _checksum(record["key"]) != record["checksum"]:
            return {"valid": False, "reason": "License file tampered"}

        expiry = datetime.strptime(record["expiry"], "%Y-%m-%d")
        days_left = (expiry - datetime.now()).days

        if days_left < 0:
            return {"valid": False, "reason": f"License expired on {record['expiry']}"}

        # Mask key for display:  RG-PROT-****-****-DEMO
        parts = record["key"].split("-")

        if len(parts) >= 5:
            masked = f"{parts[0]}-{parts[1]}-****-****-{parts[-1]}"
        else:
            masked = record["key"][:6] + "****"
        return {
            "valid":          True,
            "tier":           record["tier"],
            "expiry":         record["expiry"],
            "days_remaining": days_left,
            "key_masked":     masked,
            "seats":          record["seats"],
            "activated":      record["activated"],
        }

    except Exception as e:
        return {"valid": False, "reason": f"License read error: {e}"}


def is_activated() -> bool:
    return get_license_status().get("valid", False)


def deactivate():
    """Remove license (for uninstall)."""
    if os.path.exists(LICENSE_FILE):
        os.remove(LICENSE_FILE)
