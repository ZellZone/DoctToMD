#!/usr/bin/env python3
"""DOCX → Markdown desktop app."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import collect_docx_files, convert_docx_to_md, default_output_path


APP_TITLE = "DocxToMD"
WINDOW_SIZE = "720x520"


def resource_path(*parts: str) -> Path:
    """Resolve asset paths for source runs and PyInstaller builds."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(640, 440)
        self._apply_icon()

        self.files: list[Path] = []
        self.out_dir: Path | None = None
        self._busy = False

        self._build_ui()
        self._set_status("準備就緒：加入 .docx 檔案後按「開始轉換」")

    def _apply_icon(self) -> None:
        icon_path = resource_path("assets", "icon.ico")
        if not icon_path.is_file():
            return
        try:
            self.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(4, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Word (.docx) → Markdown (.md)",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="可一次轉換多個檔案，也可整資料夾加入。",
            foreground="#555555",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        list_frame = ttk.LabelFrame(root, text="待轉換檔案", padding=8)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            activestyle="dotbox",
            font=("Consolas", 10),
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        btns = ttk.Frame(root)
        btns.grid(row=2, column=0, sticky="ew", pady=12)
        for i in range(5):
            btns.columnconfigure(i, weight=0)
        btns.columnconfigure(5, weight=1)

        ttk.Button(btns, text="加入檔案…", command=self.add_files).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="加入資料夾…", command=self.add_folder).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(btns, text="移除選取", command=self.remove_selected).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(btns, text="清空列表", command=self.clear_files).grid(row=0, column=3, padx=(0, 8))

        options = ttk.LabelFrame(root, text="選項", padding=10)
        options.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        options.columnconfigure(1, weight=1)

        self.extract_images = tk.BooleanVar(value=True)
        self.recursive = tk.BooleanVar(value=False)
        self.open_after = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            options,
            text="匯出圖片到「檔名_media」資料夾",
            variable=self.extract_images,
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Checkbutton(
            options,
            text="加入資料夾時包含子目錄",
            variable=self.recursive,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

        ttk.Checkbutton(
            options,
            text="完成後開啟輸出資料夾",
            variable=self.open_after,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        ttk.Label(options, text="輸出資料夾：").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.out_dir_var = tk.StringVar(value="（與來源檔同目錄）")
        ttk.Entry(options, textvariable=self.out_dir_var, state="readonly").grid(
            row=3, column=1, sticky="ew", padx=8, pady=(10, 0)
        )
        ttk.Button(options, text="選擇…", command=self.choose_out_dir).grid(
            row=3, column=2, sticky="e", pady=(10, 0)
        )
        ttk.Button(options, text="重設", command=self.reset_out_dir).grid(
            row=3, column=3, sticky="e", padx=(8, 0), pady=(10, 0)
        )

        log_frame = ttk.LabelFrame(root, text="轉換紀錄", padding=8)
        log_frame.grid(row=4, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log = tk.Text(log_frame, height=8, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED)
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=log_scroll.set)

        bottom = ttk.Frame(root)
        bottom.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        bottom.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar()
        ttk.Label(bottom, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

        self.convert_btn = ttk.Button(bottom, text="開始轉換", command=self.start_convert)
        self.convert_btn.grid(row=0, column=1, sticky="e")

        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.grid(row=6, column=0, sticky="ew", pady=(10, 0))

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _append_log(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for path in self.files:
            self.listbox.insert(tk.END, str(path))
        self._set_status(f"已加入 {len(self.files)} 個檔案")

    def _add_paths(self, paths: list[Path]) -> None:
        new_files = collect_docx_files(paths, recursive=self.recursive.get())
        if not new_files:
            messagebox.showinfo(APP_TITLE, "沒有找到 .docx 檔案。")
            return

        existing = set(self.files)
        added = [p for p in new_files if p not in existing]
        self.files.extend(added)
        self.files = sorted(set(self.files))
        self._refresh_list()
        if added:
            self._append_log(f"新增 {len(added)} 個檔案")

    def add_files(self) -> None:
        if self._busy:
            return
        selected = filedialog.askopenfilenames(
            title="選擇 Word 文件",
            filetypes=[("Word 文件", "*.docx"), ("所有檔案", "*.*")],
        )
        if selected:
            self._add_paths([Path(p) for p in selected])

    def add_folder(self) -> None:
        if self._busy:
            return
        folder = filedialog.askdirectory(title="選擇包含 .docx 的資料夾")
        if folder:
            self._add_paths([Path(folder)])

    def remove_selected(self) -> None:
        if self._busy:
            return
        indexes = list(self.listbox.curselection())
        if not indexes:
            return
        for index in reversed(indexes):
            del self.files[index]
        self._refresh_list()

    def clear_files(self) -> None:
        if self._busy:
            return
        self.files.clear()
        self._refresh_list()

    def choose_out_dir(self) -> None:
        if self._busy:
            return
        folder = filedialog.askdirectory(title="選擇輸出資料夾")
        if folder:
            self.out_dir = Path(folder)
            self.out_dir_var.set(str(self.out_dir))

    def reset_out_dir(self) -> None:
        if self._busy:
            return
        self.out_dir = None
        self.out_dir_var.set("（與來源檔同目錄）")

    def start_convert(self) -> None:
        if self._busy:
            return
        if not self.files:
            messagebox.showwarning(APP_TITLE, "請先加入至少一個 .docx 檔案。")
            return

        self._busy = True
        self.convert_btn.configure(state=tk.DISABLED)
        self.progress.configure(maximum=len(self.files), value=0)
        self._append_log("—— 開始轉換 ——")
        self._set_status("轉換中…")

        thread = threading.Thread(target=self._convert_worker, daemon=True)
        thread.start()

    def _convert_worker(self) -> None:
        ok = 0
        failed = 0
        output_dirs: set[Path] = set()

        for index, input_path in enumerate(self.files, start=1):
            output_path = default_output_path(input_path, self.out_dir)
            try:
                messages = convert_docx_to_md(
                    input_path,
                    output_path,
                    extract_images=self.extract_images.get(),
                )
                ok += 1
                output_dirs.add(output_path.parent)
                line = f"[完成] {input_path.name} → {output_path}"
                for msg in messages:
                    line += f"\n  警告: {msg}"
            except Exception as exc:  # noqa: BLE001
                failed += 1
                line = f"[失敗] {input_path.name} → {exc}"

            self.after(0, self._on_file_done, index, line)

        self.after(0, self._on_all_done, ok, failed, output_dirs)

    def _on_file_done(self, index: int, line: str) -> None:
        self.progress.configure(value=index)
        self._append_log(line)
        self._set_status(f"轉換中… {index}/{len(self.files)}")

    def _on_all_done(self, ok: int, failed: int, output_dirs: set[Path]) -> None:
        self._busy = False
        self.convert_btn.configure(state=tk.NORMAL)
        summary = f"完成 {ok} 個，失敗 {failed} 個"
        self._append_log(summary)
        self._append_log("—— 結束 ——")
        self._set_status(summary)

        if self.open_after.get() and ok > 0 and output_dirs:
            # Open the single output folder, or the first one if mixed.
            folder = next(iter(sorted(output_dirs)))
            self._open_folder(folder)

        if failed == 0:
            messagebox.showinfo(APP_TITLE, summary)
        else:
            messagebox.showwarning(APP_TITLE, summary)

    @staticmethod
    def _open_folder(folder: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except OSError:
            pass


def main() -> int:
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
