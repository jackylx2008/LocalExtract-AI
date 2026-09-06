"""Tkinter 桌面界面。"""

from __future__ import annotations

import logging
import platform
import queue
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, scrolledtext, ttk
from typing import Any

from flows.extract_clipboard_flow import TaskCancelled, run as run_extraction, verify_ai
from local_extract_ai.context import AppContext


@dataclass(slots=True)
class UIMessage:
    kind: str
    payload: Any


class QueueLogHandler(logging.Handler):
    def __init__(self, messages: queue.Queue[UIMessage]) -> None:
        super().__init__()
        self.messages = messages
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.put(UIMessage("log", (record.levelname, self.format(record))))


class LocalExtractApp:
    POLL_MS = 80

    def __init__(self, context: AppContext) -> None:
        self.context = context
        self.root = tk.Tk()
        self.root.title(str(context.config["app"].get("window_title", "LocalExtract AI")))
        self.root.geometry("920x680")
        self.root.minsize(760, 560)
        self.messages: queue.Queue[UIMessage] = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.started_at: float | None = None
        self.max_log_lines = int(context.config["app"].get("max_gui_log_lines", 1000))
        self.status_var = tk.StringVar(value="正在验证本地 AI…")
        self.detail_var = tk.StringVar(value="就绪")
        self.elapsed_var = tk.StringVar(value="耗时 00:00:00")
        self.ai_status_var = tk.StringVar(value="本地 AI：验证中")
        self.progress_var = tk.DoubleVar(value=0)
        self._build_ui()
        self._attach_log_handler()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(self.POLL_MS, self._drain_messages)
        self._start_verification()

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=3)
        self.root.rowconfigure(2, weight=2)

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        extract_tab = ttk.Frame(notebook, padding=14)
        config_tab = ttk.Frame(notebook, padding=14)
        notebook.add(extract_tab, text="截图识别")
        notebook.add(config_tab, text="全局配置")
        self._build_extract_tab(extract_tab)
        self._build_config_tab(config_tab)

        action_frame = ttk.LabelFrame(self.root, text="任务操作", padding=(10, 8))
        action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        action_frame.columnconfigure(1, weight=1)
        self.preview_button = ttk.Button(action_frame, text="参数预览", command=self._preview)
        self.preview_button.grid(row=0, column=0, padx=(0, 8))
        self.start_button = ttk.Button(
            action_frame,
            text="开始识别",
            command=self._start_extraction,
            width=24,
            state=tk.DISABLED,
        )
        self.start_button.grid(row=0, column=1, padx=8)
        self.cancel_button = ttk.Button(action_frame, text="取消任务", command=self._cancel, state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=2, padx=(8, 0))

        log_frame = ttk.LabelFrame(self.root, text="运行日志与实时输出", padding=(8, 6))
        log_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.tag_configure("INFO", foreground="#202020")
        self.log_text.tag_configure("WARNING", foreground="#9a6700")
        self.log_text.tag_configure("ERROR", foreground="#b42318")
        self.log_text.tag_configure("SUCCESS", foreground="#137333")
        ttk.Button(log_frame, text="清空日志", command=self._clear_log).grid(row=1, column=0, sticky="e", pady=(6, 0))

        status = ttk.Frame(self.root, padding=(10, 4, 10, 8))
        status.grid(row=3, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        ttk.Progressbar(status, variable=self.progress_var, maximum=100).grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 5))
        ttk.Label(status, textvariable=self.status_var).grid(row=1, column=0, sticky="w")
        ttk.Label(status, textvariable=self.detail_var).grid(row=1, column=1, padx=12)
        ttk.Label(status, textvariable=self.elapsed_var).grid(row=1, column=2, padx=12)
        runtime = f"Python {sys.version_info.major}.{sys.version_info.minor} / Tk {tk.TkVersion} / {platform.system()}"
        ttk.Label(status, text=runtime).grid(row=1, column=3, sticky="e")

    def _build_extract_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(1, weight=1)
        ttk.Label(tab, text="输入来源").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(tab, text="Windows 剪贴板中的截图").grid(row=0, column=1, sticky="w", pady=6)
        ttk.Label(tab, text="AI 状态").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Label(tab, textvariable=self.ai_status_var).grid(row=1, column=1, sticky="w", pady=6)
        ttk.Label(tab, text="操作说明").grid(row=2, column=0, sticky="nw", pady=6)
        instructions = "1. 使用 Win+Shift+S 截图\n2. 回到此窗口点击“开始识别”\n3. 识别结果会替换剪贴板内容，可直接粘贴"
        ttk.Label(tab, text=instructions, justify=tk.LEFT).grid(row=2, column=1, sticky="w", pady=6)

    def _build_config_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(1, weight=1)
        ai = self.context.config["ai"]
        values = (
            ("服务地址", ai["base_url"]),
            ("模型", ai["model"]),
            ("请求超时", f"{ai.get('timeout_seconds', 60)} 秒"),
            ("配置来源", "config.yaml / common.env"),
        )
        for row, (label, value) in enumerate(values):
            ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=8)
            entry = ttk.Entry(tab)
            entry.insert(0, str(value))
            entry.configure(state="readonly")
            entry.grid(row=row, column=1, sticky="ew", pady=8)
        ttk.Label(tab, text="配置修改后请重新启动应用。密钥不会显示在界面中。", foreground="#666666").grid(
            row=len(values), column=0, columnspan=2, sticky="w", pady=(14, 0)
        )

    def _attach_log_handler(self) -> None:
        handler = QueueLogHandler(self.messages)
        logging.getLogger().addHandler(handler)
        self.gui_log_handler = handler

    def _start_verification(self) -> None:
        threading.Thread(target=self._verify_worker, daemon=True, name="ai-verification").start()

    def _verify_worker(self) -> None:
        try:
            message = verify_ai(self.context)
            self.messages.put(UIMessage("verified", (True, message)))
        except Exception as exc:
            self.messages.put(UIMessage("verified", (False, str(exc))))

    def _preview(self) -> None:
        ai = self.context.config["ai"]
        prompt = self.context.config["flows"]["extract_clipboard"]["prompt"]
        messagebox.showinfo("参数预览", f"AI 地址：{ai['base_url']}\n模型：{ai['model']}\n\n识别要求：\n{prompt}")

    def _start_extraction(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        self.cancel_event.clear()
        self.started_at = time.monotonic()
        self.progress_var.set(0)
        self.status_var.set("运行")
        self.detail_var.set("准备读取剪贴板")
        self.start_button.configure(state=tk.DISABLED)
        self.preview_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.worker = threading.Thread(target=self._extraction_worker, daemon=True, name="clipboard-extraction")
        self.worker.start()

    def _extraction_worker(self) -> None:
        try:
            result = run_extraction(
                self.context,
                self.cancel_event,
                lambda value, text: self.messages.put(UIMessage("progress", (value, text))),
            )
            self.messages.put(UIMessage("completed", result))
        except TaskCancelled as exc:
            self.messages.put(UIMessage("cancelled", str(exc)))
        except Exception as exc:
            logging.getLogger(__name__).exception("截图识别失败")
            self.messages.put(UIMessage("failed", str(exc)))

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.status_var.set("正在取消")
        self.detail_var.set("将在当前安全阶段结束后取消")
        self.cancel_button.configure(state=tk.DISABLED)

    def _drain_messages(self) -> None:
        try:
            while True:
                message = self.messages.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass
        if self.started_at is not None and self.worker and self.worker.is_alive():
            self.elapsed_var.set(f"耗时 {self._format_elapsed(time.monotonic() - self.started_at)}")
        self.root.after(self.POLL_MS, self._drain_messages)

    def _handle_message(self, message: UIMessage) -> None:
        if message.kind == "log":
            level, text = message.payload
            self._append_log(text, level)
        elif message.kind == "verified":
            ok, text = message.payload
            self.ai_status_var.set(text if ok else f"不可用：{text}")
            self.status_var.set("就绪" if ok else "失败")
            self.detail_var.set("可开始识别" if ok else "请检查本地 AI 服务与配置")
            self.start_button.configure(state=tk.NORMAL if ok else tk.DISABLED)
            self._append_log(text, "SUCCESS" if ok else "ERROR")
        elif message.kind == "progress":
            value, text = message.payload
            self.progress_var.set(value)
            self.detail_var.set(text)
        elif message.kind == "completed":
            result = message.payload
            self._finish("完成", f"已复制 {len(result.text)} 个字符", 100)
            self._append_log(f"识别成功（截图 {result.width}×{result.height}），结果已写入剪贴板", "SUCCESS")
        elif message.kind == "cancelled":
            self._finish("已取消", str(message.payload), self.progress_var.get())
        elif message.kind == "failed":
            self._finish("失败", str(message.payload), self.progress_var.get())
            messagebox.showerror("识别失败", str(message.payload))

    def _finish(self, status: str, detail: str, progress: float) -> None:
        elapsed = time.monotonic() - self.started_at if self.started_at is not None else 0
        self.status_var.set(status)
        self.detail_var.set(detail)
        self.progress_var.set(progress)
        self.elapsed_var.set(f"耗时 {self._format_elapsed(elapsed)}")
        self.started_at = None
        self.start_button.configure(state=tk.NORMAL)
        self.preview_button.configure(state=tk.NORMAL)
        self.cancel_button.configure(state=tk.DISABLED)

    def _append_log(self, text: str, tag: str = "INFO") -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n", tag if tag in ("INFO", "WARNING", "ERROR", "SUCCESS") else "INFO")
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > self.max_log_lines:
            self.log_text.delete("1.0", f"{line_count - self.max_log_lines + 1}.0")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_close(self) -> None:
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno("任务仍在运行", "关闭窗口后任务将在后台结束，确定关闭吗？"):
                return
            self.cancel_event.set()
        logging.getLogger().removeHandler(self.gui_log_handler)
        self.root.destroy()

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        total = max(0, int(seconds))
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
