"""Cửa sổ cục bộ tối thiểu cho Owner chạy Reports trên macOS.

S069: mở rộng launcher V1 (chọn file → chạy → xem kết quả → mở Excel) thêm
data readiness, Review summary, feedback local và telemetry aggregate local.
UI ở đây chỉ trình bày lại đúng số đã có trong ``ReportSummary`` — không tự
tính lại, không tự phân loại lại business reason.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

REPO_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO_ROOT))

from app import beta_feedback, beta_telemetry
from app.beta_presentation import format_review_reasons
from app.owner_usability import (
    OwnerUsabilityError, open_report_file, run_owner_report, select_latest_valid_captures,
)


class OwnerLauncher:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Reports")
        root.resizable(False, False)
        self.sales_path = tk.StringVar()
        self.status = tk.StringVar(value="Chọn workbook kế toán để bắt đầu.")
        self.readiness = tk.StringVar()
        self.result_text = tk.StringVar(value="")
        self.review_text = tk.StringVar(value="")
        self._last_output: Optional[Path] = None
        self._last_run_id: Optional[str] = None

        frame = ttk.Frame(root, padding=20)
        frame.grid(sticky="nsew")
        ttk.Label(frame, text="Tạo báo cáo Reports", font=("Helvetica", 16, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )
        ttk.Label(frame, textvariable=self.readiness).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )
        ttk.Label(frame, text="Workbook kế toán (.xlsx)").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.sales_path, width=50, state="readonly").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(4, 0)
        )
        ttk.Button(frame, text="Chọn workbook…", command=self.choose_sales).grid(
            row=3, column=2, padx=(8, 0)
        )
        self.run_button = ttk.Button(frame, text="CHẠY BÁO CÁO", command=self.run, state="disabled")
        self.run_button.grid(row=4, column=0, sticky="w", pady=(16, 4))
        ttk.Label(frame, textvariable=self.status, wraplength=480, justify="left").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )
        ttk.Label(frame, textvariable=self.result_text, wraplength=480, justify="left").grid(
            row=6, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(frame, textvariable=self.review_text, wraplength=480, justify="left").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(4, 8)
        )
        actions = ttk.Frame(frame)
        actions.grid(row=8, column=0, columnspan=3, sticky="w")
        self.open_button = ttk.Button(
            actions, text="Mở báo cáo Excel", command=self.open_output, state="disabled"
        )
        self.open_button.grid(row=0, column=0)
        ttk.Button(actions, text="Gửi phản hồi", command=self.open_feedback_dialog).grid(
            row=0, column=1, padx=(8, 0)
        )

        self._refresh_readiness()

    def _refresh_readiness(self) -> None:
        try:
            select_latest_valid_captures()
        except OwnerUsabilityError:
            self.readiness.set("Dữ liệu Tracking: Chưa sẵn sàng")
        except Exception:
            self.readiness.set("Dữ liệu Tracking: Chưa sẵn sàng")
        else:
            # Chỉ xác nhận có capture COMPLETE hợp lệ trên máy — KHÔNG xác nhận
            # capture đó đủ mới cho workbook sắp chạy (temporal coverage do
            # production path tự kiểm khi chạy, an toàn fail-safe về Pending).
            self.readiness.set("Dữ liệu Tracking: Có capture hợp lệ trên máy")

    def choose_sales(self) -> None:
        selected = filedialog.askopenfilename(
            title="Chọn workbook kế toán", filetypes=[("Excel workbook", "*.xlsx")]
        )
        if selected:
            self.sales_path.set(selected)
            self.status.set(f"Đã chọn: {Path(selected).name}. Sẵn sàng chạy báo cáo.")
            self.run_button.configure(state="normal")

    def run(self) -> None:
        self._refresh_readiness()
        self.run_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.status.set("Đang xử lý...")
        self.result_text.set("")
        self.review_text.set("")
        self.root.update_idletasks()
        started = time.monotonic()
        try:
            owner_run = run_owner_report(sales=Path(self.sales_path.get()))
        except OwnerUsabilityError as exc:
            self.status.set(str(exc))
            messagebox.showerror("Không thể tạo báo cáo", str(exc), parent=self.root)
        except Exception:
            message = "Không thể tạo báo cáo. Kiểm tra workbook và thử lại."
            self.status.set(message)
            messagebox.showerror("Không thể tạo báo cáo", message, parent=self.root)
        else:
            duration_ms = int((time.monotonic() - started) * 1000)
            summary = owner_run.demo_run.summary
            self._last_output = owner_run.output_path
            self._last_run_id = owner_run.output_path.stem
            self.status.set("Báo cáo đã hoàn tất.")
            self.result_text.set(
                f"Tổng đơn: {summary.input_orders}    "
                f"AUTO: {summary.auto_orders}    "
                f"Cần xem lại: {summary.review_orders}    "
                f"Ưu tiên xem ngay: {summary.error_count}    "
                f"Accounting coverage: {summary.order_accounting_rate:.0%}"
            )
            self.review_text.set(format_review_reasons(summary.review_reason_counts))
            self.open_button.configure(state="normal")
            self._record_telemetry(summary, duration_ms)
        finally:
            self.run_button.configure(state="normal" if self.sales_path.get() else "disabled")

    def _record_telemetry(self, summary, duration_ms: int) -> None:
        # Telemetry aggregate là byproduct vận hành, không phải core path của
        # Owner. Không để một lỗi ghi telemetry chặn báo cáo Owner đã có.
        try:
            record = beta_telemetry.build_run_record(
                run_id=self._last_run_id, summary=summary,
                processing_duration_ms=duration_ms,
            )
            beta_telemetry.record_run(record)
        except Exception:
            pass

    def open_output(self) -> None:
        if self._last_output is not None:
            open_report_file(self._last_output)

    def open_feedback_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Gửi phản hồi")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        pad = ttk.Frame(dialog, padding=16)
        pad.grid(sticky="nsew")
        ttk.Label(pad, text="Loại phản hồi").grid(row=0, column=0, sticky="w")
        category = tk.StringVar(value=beta_feedback.FEEDBACK_CATEGORIES[0])
        for index, option in enumerate(beta_feedback.FEEDBACK_CATEGORIES, start=1):
            ttk.Radiobutton(pad, text=option, variable=category, value=option).grid(
                row=index, column=0, sticky="w"
            )
        note_row = len(beta_feedback.FEEDBACK_CATEGORIES) + 1
        ttk.Label(pad, text="Ghi chú (không bắt buộc)").grid(
            row=note_row, column=0, sticky="w", pady=(8, 0)
        )
        comment_box = tk.Text(pad, width=48, height=4)
        comment_box.grid(row=note_row + 1, column=0, pady=(4, 8))

        def save() -> None:
            record = beta_feedback.build_feedback_record(
                category=category.get(),
                comment=comment_box.get("1.0", "end"),
                run_id=self._last_run_id,
            )
            beta_feedback.save_feedback(record)
            dialog.destroy()
            messagebox.showinfo("Cảm ơn", "Đã lưu phản hồi.", parent=self.root)

        ttk.Button(pad, text="Lưu phản hồi", command=save).grid(
            row=note_row + 2, column=0, sticky="w"
        )


def main() -> int:
    root = tk.Tk()
    OwnerLauncher(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
