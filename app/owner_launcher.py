"""Cửa sổ cục bộ tối thiểu cho Owner chạy Reports trên macOS."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

REPO_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO_ROOT))

from app.owner_usability import OwnerUsabilityError, run_owner_report


class OwnerLauncher:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Reports")
        root.resizable(False, False)
        self.sales_path = tk.StringVar()
        self.status = tk.StringVar(value="Chọn workbook kế toán để bắt đầu.")
        self._last_output: Path | None = None

        frame = ttk.Frame(root, padding=20)
        frame.grid(sticky="nsew")
        ttk.Label(frame, text="Tạo báo cáo Reports", font=("Helvetica", 16, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )
        ttk.Label(frame, text="Workbook kế toán (.xlsx)").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.sales_path, width=50, state="readonly").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0)
        )
        ttk.Button(frame, text="Chọn workbook…", command=self.choose_sales).grid(
            row=2, column=2, padx=(8, 0)
        )
        self.run_button = ttk.Button(frame, text="Tạo báo cáo", command=self.run, state="disabled")
        self.run_button.grid(row=3, column=0, sticky="w", pady=(16, 12))
        ttk.Label(frame, textvariable=self.status, wraplength=480, justify="left").grid(
            row=4, column=0, columnspan=3, sticky="w"
        )

    def choose_sales(self) -> None:
        selected = filedialog.askopenfilename(
            title="Chọn workbook kế toán", filetypes=[("Excel workbook", "*.xlsx")]
        )
        if selected:
            self.sales_path.set(selected)
            self.status.set("Sẵn sàng tạo báo cáo. Capture COMPLETE sẽ được chọn tự động.")
            self.run_button.configure(state="normal")

    def run(self) -> None:
        self.run_button.configure(state="disabled")
        self.status.set("Đang tạo báo cáo…")
        self.root.update_idletasks()
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
            summary = owner_run.demo_run.summary
            self._last_output = owner_run.output_path
            message = (
                "Báo cáo đã hoàn tất.\n\n"
                f"Đơn hàng: {summary.input_orders}\n"
                f"AUTO: {summary.auto_orders}\n"
                f"Review Queue: {summary.review_orders}\n\n"
                f"Tệp: {owner_run.output_path}"
            )
            self.status.set(message.replace("\n", " "))
            if messagebox.askyesno("Báo cáo hoàn tất", message + "\n\nMở tệp ngay?", parent=self.root):
                subprocess.run(["open", str(owner_run.output_path)], check=False)
        finally:
            self.run_button.configure(state="normal" if self.sales_path.get() else "disabled")


def main() -> int:
    root = tk.Tk()
    OwnerLauncher(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
