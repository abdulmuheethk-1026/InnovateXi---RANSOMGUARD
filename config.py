"""
RANSOMGUARD – Configuration & Thresholds
Centralised settings for all modules.
"""

import os

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
WATCH_PATHS = [
    os.path.join(os.environ["LOCALAPPDATA"], "Temp", "rg_sim_files"),
    os.path.expanduser("~\\Documents"),
    os.path.expanduser("~\\Desktop"),
    os.path.expanduser("~\\Downloads"),
    
]

BACKUP_ROOT   = os.path.join(os.getcwd(), "Backups")
LOG_DIR       = "C:\\RansomGuard_Logs"
CONFIG_FILE   = "C:\\RansomGuard\\config.enc"
ADMIN_HASH    = "ransomguard_admin_2024"   # SHA-256 hashed in production

# ─────────────────────────────────────────────
# DETECTION THRESHOLDS  (tunable per SME size)
# ─────────────────────────────────────────────
THRESHOLDS = {
    "rename_per_minute":         10,   # >10 renames / min → suspicious
    "modifications_per_minute":  20,   # >20 modifications / min
    "file_access_per_minute":    50,   # >50 reads / min by one process
    "ext_changes_per_minute":     5,   # >5 extension changes / min
    "risk_score_warn":           40,   # yellow alert
    "risk_score_alert":          65,   # orange alert + popup
    "risk_score_isolate":        85,   # red alert + process kill + backup
}

# ─────────────────────────────────────────────
# RANSOMWARE SIGNATURES
# ─────────────────────────────────────────────
SUSPICIOUS_PREFIXES = [
    "locked_", "encrypted_", "ransom_",
    "crypt_",  "enc_",       "crypted_",
]

SUSPICIOUS_EXTENSIONS = [
    ".locked", ".encrypted", ".crypto",
    ".enc",    ".crypt",     ".zzz",
    ".zepto",  ".cerber",    ".wncry",
    ".wcry",   ".wncryt",    ".locky",
]

# ─────────────────────────────────────────────
# ENGINE SETTINGS
# ─────────────────────────────────────────────
TIME_WINDOW_SECONDS   = 60       # sliding analysis window
SCORE_DECAY_FACTOR    = 0.85     # risk score decays each window if no new events
BACKUP_MAX_SIZE_MB    = 500      # max backup snapshot size
PROCESS_KILL_ENABLED  = True     # set False in demo/read-only mode
NETWORK_BLOCK_ENABLED = False    # requires admin + Windows Firewall API

# ─────────────────────────────────────────────
# AI SCORING WEIGHTS  (rule-based MVP)
# ─────────────────────────────────────────────
SCORE_WEIGHTS = {
    "rapid_rename":       30,
    "bulk_modification":  25,
    "ext_change":         20,
    "suspicious_prefix":  15,
    "bulk_access":        10,
}
