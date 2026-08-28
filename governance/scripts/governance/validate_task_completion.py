#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK_DIR = ROOT / "docs/tasks"
GATE_EXEC_DIR = ROOT / "docs/reviews"

VALID_CHECK_STATUS = {"NOT_TESTED", "PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"}

HASH_RE = r"`?([0-9a-fA-F]{64})`?"


def _hash_after_label(text, label):
    """Find the first 64-hex-char value bound to `label: <hash>` (same line
    or the next non-blank line, optionally backtick-wrapped). Used to
    cross-check GATE_SET_SHA256 between a frozen task file and a Gate
    Execution Record without requiring either to declare it in an identical
    format."""
    pattern = re.compile(re.escape(label) + r"[^\n:]*:\s*\n?\s*" + HASH_RE)
    m = pattern.search(text)
    return m.group(1).lower() if m else None


def _frozen_gate_hash(task_text):
    return _hash_after_label(task_text, "GATE_SET_SHA256")


def _task_id_from_filename(filename):
    m = re.match(r"TASK-([A-Za-z0-9]+)-", filename)
    return m.group(1) if m else None


def _gate_execution_record_paths(gate_exec_dir, task_id):
    return sorted(gate_exec_dir.glob(f"TASK-{task_id}-GATE-EXECUTION-RECORD*.md"))


def _parse_gate_execution_record(path):
    text = path.read_text(encoding="utf-8")

    record_hash = _hash_after_label(text, "GATE_SET_SHA256")

    executed_by_match = re.search(r"(?mi)^\s*Executed By:\s*\n\s*(\S.*)$", text)
    lineage_ok = bool(executed_by_match and executed_by_match.group(1).strip())

    checks = {}
    row_re = re.compile(
        r"(?m)^\|\s*(CHECK-[A-Za-z0-9\-]+)\s*\|\s*([A-Z_]+)\s*\|\s*(E[0-2])\s*\|"
        r"\s*([^|]*)\|\s*([^|]*)\|"
    )
    for check_id, result, ev_level, run_result, test_ref in row_re.findall(text):
        evidence = f"{run_result.strip()} — {test_ref.strip()}".strip(" —")
        checks[check_id] = {
            "result": result.strip(),
            "evidence_level": ev_level.strip(),
            "evidence": evidence,
        }

    return {
        "path": path,
        "gate_hash": record_hash,
        "lineage_ok": lineage_ok,
        "checks": checks,
    }


def _resolve_via_gate_execution_record(gate_exec_dir, task_filename, frozen_hash, check_id):
    """Implements the DEC-159 / H-07 two-layer binding: a REQUIRED check whose
    frozen embedded Status is (by design, immutably) NOT_TESTED can still be
    treated as effectively satisfied if a canonical Gate Execution Record
    binds the exact frozen GATE_SET_SHA256 + exact check ID with an
    authoritative PASS. Returns (entry, None) on success, or (None, reason)
    on any failure — every failure path is fail-closed (no effective PASS).
    """
    if not frozen_hash:
        return None, "task file has no frozen GATE_SET_SHA256 to bind against"

    task_id = _task_id_from_filename(task_filename)
    if not task_id:
        return None, "cannot derive task ID from filename"

    record_paths = _gate_execution_record_paths(gate_exec_dir, task_id)
    if not record_paths:
        return None, "no Gate Execution Record found"

    records = [_parse_gate_execution_record(p) for p in record_paths]

    bound = [
        r for r in records
        if r["gate_hash"] and r["gate_hash"] == frozen_hash and check_id in r["checks"]
    ]
    mismatched = [
        r for r in records
        if check_id in r["checks"] and (not r["gate_hash"] or r["gate_hash"] != frozen_hash)
    ]

    if not bound:
        if mismatched:
            return None, "Gate Execution Record exists but GATE_SET_SHA256 does not match frozen gate"
        return None, "check ID not present in any Gate Execution Record"

    results = {r["checks"][check_id]["result"] for r in bound}
    if len(results) > 1:
        return None, "duplicate/ambiguous authoritative Gate Execution Records disagree for this check"

    chosen = bound[0]
    entry = chosen["checks"][check_id]

    if entry["result"] != "PASS":
        return None, f"authoritative Gate Execution Record reports {entry['result']}"

    if not chosen["lineage_ok"]:
        return None, "Gate Execution Record missing implementation/review lineage (Executed By)"

    if entry["evidence_level"] not in {"E0", "E1", "E2"}:
        return None, "Gate Execution Record missing valid Evidence Level"

    if not entry["evidence"].strip() or entry["evidence"].strip() == "—":
        return None, "Gate Execution Record missing concrete Evidence"

    return entry, None


def run_validation(task_dir=TASK_DIR, gate_exec_dir=GATE_EXEC_DIR):
    task_files = sorted(task_dir.glob("TASK-*.md"))
    errors = []
    checked_done = 0

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

        frozen_hash = _frozen_gate_hash(txt)

        # Approximate check blocks by markdown headings. Templates use CHECK-* headings.
        blocks = re.split(r"(?m)^####?\s+", txt)

        required_blocks_seen = 0
        for block in blocks:
            if not re.search(r"(?mi)^\s*Priority:\s*REQUIRED\s*$", block):
                continue

            required_blocks_seen += 1
            lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            check_name = lines[0] if lines else "UNKNOWN_CHECK"
            # Heading text is often "CHECK-105D-01 (G01) — description", not
            # a bare ID. Gate Execution Record tables key on the bare ID, so
            # extract just the leading CHECK-<...> token for that lookup.
            check_id_match = re.match(r"(CHECK-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)", check_name)
            check_id = check_id_match.group(1) if check_id_match else check_name

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

            if state == "NOT_TESTED":
                # Layer 2 (DEC-159): a frozen check's embedded Status is
                # designed to stay NOT_TESTED forever (mutating it would
                # change GATE_SET_SHA256). Fall back to the canonical Gate
                # Execution Record before declaring this a hard failure.
                resolved, reason = _resolve_via_gate_execution_record(
                    gate_exec_dir, path.name, frozen_hash, check_id
                )
                if resolved is None:
                    errors.append(
                        f"{path.name}: DONE task contains REQUIRED check '{check_name}' "
                        f"with Status=NOT_TESTED and no valid Gate Execution Record "
                        f"({reason})."
                    )
                    continue
                # Effective PASS via Layer 2 — evidence already validated
                # inside _resolve_via_gate_execution_record.
                continue

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

    return errors, checked_done


if __name__ == "__main__":
    errors, checked_done = run_validation()

    if errors:
        print("TASK COMPLETION: FAIL")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)

    print("TASK COMPLETION: PASS")
    print(f"Checked {checked_done} DONE task(s).")
