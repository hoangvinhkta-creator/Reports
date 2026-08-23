#!/usr/bin/env python3
"""
Regression test cho CHECK-T03-01 (TASK-REM-T03).

Kiểm chứng rằng validate_structure.py phát hiện được đúng loại lỗi từng gây
ra FIND-001: governance package bị deploy lồng trong một thư mục con thay vì
nằm ở gốc git repository.

Cách làm: tạo một bản sao validate_structure.py hiện tại vào một layout lồng
giả lập bên trong thư mục tạm (nằm NGOÀI git repository thật), rồi chạy nó
như subprocess và xác nhận nó exit khác 0 kèm thông báo rõ ràng nêu tên gốc
kỳ vọng.

Không cần .git trong fixture để tái tạo lỗi — miễn fixture nằm ngoài git
repository thật (dùng tempfile ngoài repo), find_git_root() sẽ không tìm
thấy .git nào, rơi vào nhánh NOT_APPLICABLE, không phải FAIL. Vì vậy fixture
PHẢI tự tạo .git giả (chỉ cần tồn tại, git không cần hợp lệ) tại gốc ngoài
cùng của cây thư mục lồng, để giả lập "đây là một git repo, nhưng governance
package bị deploy lồng bên trong nó".

Chạy: python3 governance/scripts/governance/fixtures/regression_nested_layout.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_UNDER_TEST = Path(__file__).resolve().parents[1] / "validate_structure.py"
WRAPPER_NAME = "SOME_WRAPPER_DIR"

# Danh sách required path của validate_structure.py — giữ đồng bộ thủ công.
# Placeholder rỗng cho từng path để cô lập failure mode: chỉ deployment-root
# được phép fail, không phải missing-required-paths.
REQUIRED_PATHS = [
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


def build_fixture(tmp_root: Path) -> Path:
    """Tạo fixture: <tmp_root>/.git (giả) + <tmp_root>/<WRAPPER>/{required paths + script}."""
    (tmp_root / ".git").mkdir()  # chỉ cần tồn tại; find_git_root() không đòi hỏi .git hợp lệ

    wrapper = tmp_root / WRAPPER_NAME
    for rel in REQUIRED_PATHS:
        target = wrapper / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# placeholder cho fixture regression test\n", encoding="utf-8")

    nested_script_dir = wrapper / "governance/scripts/governance"
    nested_script_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT_UNDER_TEST, nested_script_dir / "validate_structure.py")

    return wrapper


def main():
    with tempfile.TemporaryDirectory(prefix="regression-nested-layout-") as tmp:
        tmp_root = Path(tmp)
        wrapper = build_fixture(tmp_root)
        nested_script = wrapper / "governance/scripts/governance/validate_structure.py"

        result = subprocess.run(
            [sys.executable, str(nested_script)],
            capture_output=True,
            text=True,
        )

        print("--- output của validate_structure.py chạy trên fixture lồng ---")
        print(result.stdout)
        if result.stderr:
            print("--- stderr ---")
            print(result.stderr)

        checks = []

        checks.append(("exit code khác 0", result.returncode != 0))
        checks.append((
            "output chứa 'Deployment root: FAIL'",
            "Deployment root: FAIL" in result.stdout,
        ))
        checks.append((
            "output nêu tên gốc kỳ vọng (git root) và gốc đã resolve (ROOT)",
            "git root" in result.stdout.lower() and "resolve" in result.stdout.lower(),
        ))
        checks.append((
            "output KHÔNG báo missing required path (cô lập đúng failure mode)",
            "missing:" not in result.stdout,
        ))

        failed = [name for name, ok in checks if not ok]

        print("--- kết quả regression test ---")
        for name, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

        if failed:
            print("REGRESSION NESTED LAYOUT: FAIL")
            sys.exit(1)

        print("REGRESSION NESTED LAYOUT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
