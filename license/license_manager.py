import os
import json
import hashlib

LICENSE_FILE = os.path.join(os.getcwd(), "license", "license.json")
SECRET = "RG_DEMO_SECRET_2026"


def generate_license_key(name: str) -> str:
    raw = name.strip().upper() + SECRET
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def save_license(key: str):
    os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
    with open(LICENSE_FILE, "w") as f:
        json.dump({"license_key": key}, f)


def load_license():
    if not os.path.exists(LICENSE_FILE):
        return None
    with open(LICENSE_FILE, "r") as f:
        return json.load(f).get("license_key")


def validate_license():
    stored_key = load_license()

    if stored_key:
        return True

    print("\n🔐 RansomGuard License Activation Required")
    name = input("Enter your name: ").strip()
    user_key = input("Enter your license key: ").strip().upper()

    expected_key = generate_license_key(name)

    if user_key == expected_key:
        save_license(user_key)
        print("✅ License activated successfully.\n")
        return True
    else:
        print("❌ Invalid license key.")
        return False