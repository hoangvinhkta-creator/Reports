#!/usr/bin/env python3
"""
Regression test cho lỗi CI đã biết: `validate_reference_integrity.py` sập
với `PermissionError` khi một tài liệu trích dẫn một đường dẫn tuyệt đối
nằm trong một thư mục mà người dùng đang chạy KHÔNG đọc được (ví dụ
`/root/...` trên GitHub Actions runner, chạy bằng user không phải root) —
xem `docs/sessions/S133-r4-integration-and-deployment.md` và
`PROJECT/PROJECT_DECISIONS.md` cho bằng chứng gốc. Lỗi này đã làm sập cả
lượt quét (thay vì báo cáo một finding) trên MỌI lần chạy CI kể từ tích
hợp R4, che mất tín hiệu CI qua nhiều pull request liên tiếp.

Nguyên nhân: `Path.exists()` NÉM `PermissionError` (không tự nuốt, khác
`FileNotFoundError`/`ELOOP` mà pathlib có nuốt sẵn) khi thư mục CHA của
đường dẫn chặn quyền truy cập của người gọi — một sự thật về QUYỀN của
tiến trình đang chạy, không phải về nội dung repo. `resolves()` phải coi
đó là "không phân giải được", không phải để nó thoát ra ngoài.

Cách tái hiện KHÔNG phụ thuộc UID đang chạy fixture này:
- Nếu tiến trình đang chạy KHÔNG phải root (đúng điều kiện thật trên CI —
  GitHub Actions chạy bằng user `runner`): `os.chmod(dir, 0)` một mình đã
  đủ chặn TRUY CẬP của CHÍNH người tạo ra nó — quyền POSIX áp dụng bất kể
  ai sở hữu, trừ root.
- Nếu tiến trình đang chạy LÀ root (đúng điều kiện của một sandbox dev như
  môi trường Claude Code): root bỏ qua kiểm tra quyền POSIX thông thường,
  nên `chmod(0)` một mình không tái hiện được lỗi. Fixture tự hạ quyền
  subprocess xuống một user không đặc quyền có sẵn trên máy (`nobody` rồi
  `daemon`) trước khi thực thi validator, qua `preexec_fn`. Không tìm được
  user nào phù hợp thì báo NOT_APPLICABLE (exit 0) thay vì FAIL — đây là
  giới hạn của MÔI TRƯỜNG chạy fixture, không phải bằng chứng validator
  còn lỗi.

Chạy: python3 governance/scripts/governance/fixtures/regression_permission_denied_reference.py
"""
import os
import pwd
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_UNDER_TEST = (
    Path(__file__).resolve().parents[1] / "validate_reference_integrity.py"
)

# Ứng viên user không đặc quyền để hạ quyền xuống khi fixture tự chạy bằng
# root — thử theo thứ tự, dùng ứng viên ĐẦU TIÊN có thật trên máy.
UNPRIVILEGED_USER_CANDIDATES = ("nobody", "daemon")


def _find_unprivileged_user():
    for name in UNPRIVILEGED_USER_CANDIDATES:
        try:
            entry = pwd.getpwnam(name)
        except KeyError:
            continue
        if entry.pw_uid != 0:
            return entry
    return None


def build_fixture(tmp_root: Path) -> tuple[Path, Path]:
    """Dựng: `<tmp_root>/.git` (giả) + một file `.md` trích dẫn đường dẫn
    tuyệt đối tới một file nằm trong thư mục sẽ bị khoá quyền truy cập.

    Trả về `(git_root_gia, thu_muc_bi_khoa)` — thư mục bị khoá được trả về
    RIÊNG để `main()` chmod nó sau khi ghi xong file bên trong (khoá trước
    thì không ghi được nữa)."""
    (tmp_root / ".git").mkdir()

    blocked = tmp_root / "khong_doc_duoc"
    blocked.mkdir()
    target = blocked / "bi_khoa.md"
    target.write_text("# nội dung không bao giờ được đọc tới\n", encoding="utf-8")

    quoting_doc = tmp_root / "docs" / "trich_dan.md"
    quoting_doc.parent.mkdir(parents=True, exist_ok=True)
    quoting_doc.write_text(
        "# Tài liệu trích dẫn một đường dẫn không đọc được\n\n"
        f"Xem `{target}` để biết chi tiết.\n",
        encoding="utf-8",
    )
    return tmp_root, blocked


def _run_validator(fixture_root: Path) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT_UNDER_TEST), str(fixture_root)]
    if os.geteuid() != 0:
        # Điều kiện thật của CI: tiến trình gọi fixture này đã KHÔNG phải
        # root, nên `chmod(0)` ở `main()` đã đủ tái hiện lỗi cho chính user
        # này — không cần hạ quyền thêm.
        return subprocess.run(cmd, capture_output=True, text=True)

    unprivileged = _find_unprivileged_user()
    if unprivileged is None:
        return None  # báo hiệu "không tái hiện được ở môi trường này"

    def _drop_privileges():
        os.setgid(unprivileged.pw_gid)
        os.setuid(unprivileged.pw_uid)

    return subprocess.run(
        cmd, capture_output=True, text=True, preexec_fn=_drop_privileges
    )


def main():
    with tempfile.TemporaryDirectory(prefix="regression-perm-denied-ref-") as tmp:
        fixture_root, blocked = build_fixture(Path(tmp))
        # `mkdtemp()` tạo thư mục tạm với mode `0700` (chỉ chủ sở hữu đi
        # qua được) — đúng cho một thư mục tạm bình thường, nhưng SAI cho
        # fixture này: subprocess bị hạ quyền sẽ không đi qua nổi CHÍNH
        # `fixture_root`, và lỗi tái hiện được sẽ là "0 file .md" (không đi
        # vào được gốc) chứ không phải lỗi thật đang cần canh (không đi vào
        # được ĐÚNG MỘT thư mục con). Mở rộng quyền traversal cho mọi tổ
        # tiên, rồi khoá RIÊNG `blocked`.
        os.chmod(tmp, 0o755)
        os.chmod(fixture_root, 0o755)
        os.chmod(fixture_root / "docs", 0o755)
        try:
            os.chmod(blocked, 0)
            result = _run_validator(fixture_root)
        finally:
            # Dọn quyền trước khi `TemporaryDirectory` tự xoá cây thư mục —
            # một thư mục mode 0 có thể chặn cả chính việc xoá nó.
            os.chmod(blocked, 0o755)

        if result is None:
            print(
                "REGRESSION PERMISSION DENIED REFERENCE: NOT_APPLICABLE "
                f"— không tìm thấy user không đặc quyền nào trong "
                f"{UNPRIVILEGED_USER_CANDIDATES} để hạ quyền khi tự chạy "
                "bằng root ở môi trường này; không tái hiện được điều kiện "
                "lỗi, nhưng đó là giới hạn của máy chạy fixture, không phải "
                "bằng chứng validator còn lỗi."
            )
            sys.exit(0)

        print("--- output của validate_reference_integrity.py trên fixture ---")
        print(result.stdout)
        if result.stderr:
            print("--- stderr ---")
            print(result.stderr)

        checks = [
            (
                "không sập — exit code là 0 hoặc 1, không phải mã lỗi traceback khác",
                result.returncode in (0, 1),
            ),
            (
                "KHÔNG có traceback nào ném ra stderr",
                "Traceback" not in result.stderr and "PermissionError" not in result.stderr,
            ),
            (
                "vẫn in ra kết luận REFERENCE INTEGRITY thay vì im lặng chết",
                "REFERENCE INTEGRITY:" in result.stdout,
            ),
            (
                "đường dẫn không đọc được được báo là một finding, không bị nuốt câm",
                "khong_doc_duoc/bi_khoa.md" in result.stdout,
            ),
        ]

        failed = [name for name, ok in checks if not ok]

        print("--- kết quả regression test ---")
        for name, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

        if failed:
            print("REGRESSION PERMISSION DENIED REFERENCE: FAIL")
            sys.exit(1)

        print("REGRESSION PERMISSION DENIED REFERENCE: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
