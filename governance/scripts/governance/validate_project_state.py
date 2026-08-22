#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]

PROFILE_FILE = ROOT / "PROJECT/PROJECT_PROFILE.md"
PROGRESS_FILE = ROOT / "PROJECT/PROJECT_PROGRESS.md"

VALID_PROFILES = {"SOLO_LITE", "PRODUCT", "TEAM_PRODUCTION", "AUDIT"}
VALID_TASK_MODES = {"MICRO", "MAJOR", "SPIKE"}

errors = []

def extract_single_value(text, label):
    pattern = rf"(?mi)^\s*{re.escape(label)}\s*:\s*(?:\n\s*)?([A-Z_]+)\s*$"
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None

if not PROFILE_FILE.exists():
    errors.append("Missing PROJECT/PROJECT_PROFILE.md")
else:
    txt = PROFILE_FILE.read_text(encoding="utf-8")
    selected = extract_single_value(txt, "Selected Profile")
    if selected not in VALID_PROFILES:
        errors.append(
            "PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: "
            + ", ".join(sorted(VALID_PROFILES))
        )

if not PROGRESS_FILE.exists():
    errors.append("Missing PROJECT/PROJECT_PROGRESS.md")
else:
    txt = PROGRESS_FILE.read_text(encoding="utf-8")
    profile = extract_single_value(txt, "Profile")
    if profile not in VALID_PROFILES:
        errors.append(
            "PROJECT_PROGRESS.md must contain a valid Profile value: "
            + ", ".join(sorted(VALID_PROFILES))
        )

    task_mode = extract_single_value(txt, "Current Task Mode")
    # Current Task Mode may be blank during pure planning/audit opening,
    # but if populated it must be one of the valid values.
    if task_mode is not None and task_mode not in VALID_TASK_MODES:
        errors.append(
            "PROJECT_PROGRESS.md Current Task Mode must be MICRO, MAJOR, or SPIKE when populated."
        )

if errors:
    print("PROJECT STATE: FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("PROJECT STATE: PASS")
