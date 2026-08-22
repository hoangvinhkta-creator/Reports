#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]

required = [
    "CLAUDE.md",
    "governance/core/00_SESSION_ORCHESTRATION.md",
    "governance/core/PROJECT_PROFILE_STANDARD.md",
    "governance/core/RULE_PRECEDENCE.md",
    "governance/core/EVIDENCE_STANDARD.md",
    "governance/core/TASK_MODE_STANDARD.md",
    "governance/core/TASK_READY_GATE_STANDARD.md",
    "governance/core/TASK_COMPLETION_GATE_STANDARD.md",
    "governance/core/04_SECURITY_RULES.md",
    "governance/core/11_FORBIDDEN_ACTIONS.md",
    "PROJECT/PROJECT_PROFILE.md",
    "PROJECT/PROJECT_PROGRESS.md",
    "PROJECT/PROJECT_DECISIONS.md",
    "docs/tasks/README.md",
    "docs/sessions/README.md",
    "docs/reviews/README.md",
    "governance/templates/TASK_DEFINITION_TEMPLATE.md",
    "governance/templates/SESSION_HANDOFF_TEMPLATE.md",
    "governance/templates/PROJECT_PROGRESS_TEMPLATE.md",
    "governance/templates/MICRO_TASK_CHECKLIST.md",
    "governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md",
]

missing = [p for p in required if not (ROOT / p).exists()]

if missing:
    print("GOVERNANCE STRUCTURE: FAIL")
    for p in missing:
        print(f"- missing: {p}")
    sys.exit(1)

print("GOVERNANCE STRUCTURE: PASS")
print(f"Checked {len(required)} required paths.")
