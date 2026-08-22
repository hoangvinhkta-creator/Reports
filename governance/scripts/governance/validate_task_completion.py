#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK_DIR = ROOT / "docs/tasks"

task_files = sorted(TASK_DIR.glob("TASK-*.md"))
errors = []
checked_done = 0

VALID_CHECK_STATUS = {"NOT_TESTED", "PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"}

for path in task_files:
    txt = path.read_text(encoding="utf-8")

    status_match = re.search(r"(?mi)^\s*Status:\s*(?:\n\s*)?([A-Z_]+)\s*$", txt)
    status = status_match.group(1).strip() if status_match else None

    if status != "DONE":
        continue

    checked_done += 1

    # A DONE Major Task must contain at least one explicit REQUIRED completion check.
    # An empty/missing Completion Gate is invalid and must not pass silently.
    required_occurrences = list(re.finditer(r"(?mi)^\s*Priority:\s*REQUIRED\s*$", txt))
    if not required_occurrences:
        errors.append(
            f"{path.name}: Status=DONE but no REQUIRED Completion Gate checks were found."
        )
        continue

    # Approximate check blocks by markdown headings. Templates use CHECK-* headings.
    blocks = re.split(r"(?m)^####?\s+", txt)

    required_blocks_seen = 0
    for block in blocks:
        if not re.search(r"(?mi)^\s*Priority:\s*REQUIRED\s*$", block):
            continue

        required_blocks_seen += 1
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        check_name = lines[0] if lines else "UNKNOWN_CHECK"

        st = re.search(
            r"(?mi)^\s*Status:\s*(NOT_TESTED|PASS|FAIL|BLOCKED|NOT_APPLICABLE)\s*$",
            block,
        )
        ev_level = re.search(r"(?mi)^\s*Evidence Level:\s*(E0|E1|E2)\s*$", block)
        evidence = re.search(
            r"(?mis)^\s*Evidence:\s*\n?(.*?)(?=^\s*(?:Executed By|Timestamp|##|###|####)\s*:?\s*$|\Z)",
            block,
        )

        if not st:
            errors.append(
                f"{path.name}: REQUIRED check '{check_name}' has no valid Status."
            )
            continue

        state = st.group(1)

        # NOT_APPLICABLE is not a PASS. A REQUIRED check can only allow N/A
        # if the task gate explicitly changed before implementation. DONE task
        # validation therefore rejects N/A here rather than guessing waiver validity.
        if state != "PASS":
            errors.append(
                f"{path.name}: DONE task contains REQUIRED check '{check_name}' with Status={state}."
            )
            continue

        if not ev_level:
            errors.append(
                f"{path.name}: PASS REQUIRED check '{check_name}' missing Evidence Level."
            )

        if evidence:
            evidence_text = evidence.group(1).strip()
            if not evidence_text or evidence_text == "...":
                errors.append(
                    f"{path.name}: PASS REQUIRED check '{check_name}' missing concrete Evidence."
                )
        else:
            errors.append(
                f"{path.name}: PASS REQUIRED check '{check_name}' missing Evidence field."
            )

    # Defensive check in case Priority tokens were present but parser could not form blocks.
    if required_blocks_seen == 0:
        errors.append(
            f"{path.name}: REQUIRED gate markers exist but no parseable REQUIRED check blocks were found."
        )

if errors:
    print("TASK COMPLETION: FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("TASK COMPLETION: PASS")
print(f"Checked {checked_done} DONE task(s).")
