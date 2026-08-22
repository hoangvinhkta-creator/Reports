#!/usr/bin/env python3
"""
Optional preservation check for this compact package.

Compares selected semantic source-of-truth files against a sibling or supplied
non-compact V3.2 Final directory after normalizing compact path prefixes.

Usage:
    python governance/scripts/governance/validate_refactor_preservation.py /path/to/AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
if len(sys.argv) != 2:
    print("USAGE: validate_refactor_preservation.py <non-compact-v3.2-final-dir>")
    sys.exit(2)

SRC = Path(sys.argv[1]).resolve()
if not SRC.exists():
    print(f"PRESERVATION: FAIL\n- source does not exist: {SRC}")
    sys.exit(1)

pairs = [
    ("PROJECT_PROFILE_STANDARD.md", "governance/core/PROJECT_PROFILE_STANDARD.md"),
]

# CLAUDE has one intentional Compact Directory Layout note, so lifecycle/conflict
# semantics are tested explicitly rather than byte-for-byte.
errors = []

def normalize_paths(text: str) -> str:
    text = re.sub(r"governance/core/([A-Za-z0-9_.-]+\.md)", r"\1", text)
    text = re.sub(r"governance/product/([A-Za-z0-9_.-]+\.md)", r"\1", text)
    text = re.sub(r"governance/audit/([A-Za-z0-9_.-]+\.md)", r"\1", text)
    text = re.sub(r"governance/templates/([A-Za-z0-9_.-]+\.md)", r"templates/\1", text)
    text = re.sub(r"governance/scripts/governance/([A-Za-z0-9_.-]+\.py)", r"scripts/governance/\1", text)
    return text

for old_rel, new_rel in pairs:
    old = (SRC/old_rel).read_text(encoding="utf-8")
    new = (ROOT/new_rel).read_text(encoding="utf-8")
    if normalize_paths(new).strip() != old.strip():
        errors.append(f"semantic drift detected: {old_rel} -> {new_rel}")

claude = (ROOT/"CLAUDE.md").read_text(encoding="utf-8")
for required in [
    "NOT_PLANNED",
    "PLANNED",
    "READY",
    "IN_PROGRESS",
    "IMPLEMENTED",
    "VERIFYING",
    "DONE",
    "BLOCKED",
    "DEFERRED",
    "CANCELLED",
    "CONFLICT DETECTED",
]:
    if required not in claude:
        errors.append(f"CLAUDE.md missing required semantic token: {required}")

if errors:
    print("PRESERVATION: FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("PRESERVATION: PASS")
print("Profile selection content preserved; lifecycle/conflict mechanisms present.")
