import os
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FOLDER = os.path.join(BASE_DIR, "..", "test_documents")

RENAME_PREFIX = "locked_"
DELAY_BETWEEN_FILES = 0.3
MAX_FILES = 10

print("=== RANSOMGUARD ATTACK SIMULATION STARTED ===")
print("Simulation Time:", datetime.now())
print("---------------------------------------------")

file_count = 0

for filename in os.listdir(TARGET_FOLDER):

    if file_count >= MAX_FILES:
        print("[SAFEGUARD] File limit reached. Stopping simulation.")
        break

    old_path = os.path.join(TARGET_FOLDER, filename)

    if filename.startswith(RENAME_PREFIX):
        continue

    try:
        with open(old_path, "r", errors="ignore") as file:
            file.read()

        print(f"[ACCESS] File accessed: {filename}")

        new_name = RENAME_PREFIX + filename
        new_path = os.path.join(TARGET_FOLDER, new_name)

        os.rename(old_path, new_path)
        print(f"[RENAME] {filename}  -->  {new_name}")

        file_count += 1
        time.sleep(DELAY_BETWEEN_FILES)

    except Exception as e:
        print(f"[ERROR] Could not process {filename}: {e}")

print("---------------------------------------------")
print("=== ATTACK SIMULATION COMPLETED SAFELY ===")
