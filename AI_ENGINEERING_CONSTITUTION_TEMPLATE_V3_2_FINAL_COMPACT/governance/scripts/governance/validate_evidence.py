#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK_DIR = ROOT / "docs/tasks"

errors = []
checked = 0

for path in sorted(TASK_DIR.glob("TASK-*.md")):
    txt = path.read_text(encoding="utf-8")

    risk_m = re.search(r"(?mi)^\s*Risk:\s*(?:\n\s*)?([1-5])(?:/5)?\s*$", txt)
    risk = int(risk_m.group(1)) if risk_m else None
    if risk is None:
        continue

    blocks = re.split(r"(?m)^####?\s+", txt)
    for block in blocks:
        if not re.search(r"(?mi)^\s*Priority:\s*REQUIRED\s*$", block):
            continue

        st = re.search(r"(?mi)^\s*Status:\s*(NOT_TESTED|PASS|FAIL|BLOCKED|NOT_APPLICABLE)\s*$", block)
        if not st or st.group(1) != "PASS":
            continue

        checked += 1
        check_name = block.splitlines()[0].strip() if block.splitlines() else "UNKNOWN_CHECK"
        ev = re.search(r"(?mi)^\s*Evidence Level:\s*(E0|E1|E2)\s*$", block)
        level = ev.group(1) if ev else None

        if risk >= 3 and level not in {"E1", "E2"}:
            errors.append(
                f"{path.name}: Risk {risk} REQUIRED PASS check '{check_name}' must use E1 or E2."
            )

        ex = re.search(r"(?mi)^\s*Executed By:\s*(.+?)\s*$", block)
        ts = re.search(r"(?mi)^\s*Timestamp:\s*(.+?)\s*$", block)

        if level in {"E1", "E2"}:
            if not ex or ex.group(1).strip() in {"", "..."}:
                errors.append(f"{path.name}: '{check_name}' {level} missing Executed By.")
            if not ts or ts.group(1).strip() in {"", "..."}:
                errors.append(f"{path.name}: '{check_name}' {level} missing Timestamp.")

if errors:
    print("EVIDENCE VALIDATION: FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("EVIDENCE VALIDATION: PASS")
print(f"Checked {checked} REQUIRED PASS evidence record(s).")
