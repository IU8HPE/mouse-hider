from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import autostart
from config_manager import ConfigManager, DEFAULT_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS, MIN_TIMEOUT_SECONDS
from cursor_monitor_lite import MouseInactivityMonitorLite


AUTOSTART_APP_NAME = "MouseHiderLite32"
AUTO_MINIMIZE_DELAY_MS = 5000


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


class MouseHiderLiteApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("HPE - Mouse Hider Lite")
        self.root.configure(bg="#0b1220")
        self.root.minsize(360, 300)

        self._config_manager = ConfigManager(get_app_dir() / "config.json")
        self._config = self._config_manager.load()
        self._loading_ui = True
        self._last_monitor_status = "Stopped"
        self._auto_minimize_job: str | None = None

        self._build_ui()

        self._monitor = MouseInactivityMonitorLite(
            root=self.root,
            timeout_seconds=self._config.timeout_seconds,
            on_status_changed=self._set_status,
            on_error=self._show_error,
            on_running_changed=self._on_running_changed,
        )

        self._apply_config_to_ui()
        self._loading_ui = False
        self._set_status("Stopped")

        if self._config.start_monitoring_on_launch:
            self._monitor.start()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        panel = tk.Frame(
            self.root,
            bg="#111827",
            highlightthickness=1,
            highlightbackground="#273449",
            bd=0,
            padx=14,
            pady=14,
        )
        panel.pack(fill="both", expand=True, padx=14, pady=14)

        title = tk.Label(
            panel,
            text="Mouse Hider Lite",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        title.pack(fill="x")

        timeout_row = tk.Frame(panel, bg="#111827")
        timeout_row.pack(fill="x", pady=(10, 8))

        timeout_label = tk.Label(
            timeout_row,
            text="Idle timeout:",
            bg="#111827",
            fg="#d7e0ef",
            font=("Segoe UI", 10),
        )
        timeout_label.pack(side="left")

        self.timeout_var = tk.IntVar(value=DEFAULT_TIMEOUT_SECONDS)
        self.timeout_spin = tk.Spinbox(
            timeout_row,
            from_=MIN_TIMEOUT_SECONDS,
            to=MAX_TIMEOUT_SECONDS,
            width=5,
            textvariable=self.timeout_var,
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            buttonbackground="#1f2937",
            relief="flat",
            justify="center",
            command=self._on_timeout_changed,
        )
        self.timeout_spin.pack(side="left", padx=(10, 6))

        timeout_suffix = tk.Label(
            timeout_row,
            text="s",
            bg="#111827",
            fg="#d7e0ef",
            font=("Segoe UI", 10),
        )
        timeout_suffix.pack(side="left")

        self.start_stop_button = tk.Button(
            panel,
            text="Start",
            command=self._toggle_monitoring,
            bg="#14b8a6",
            fg="#03221e",
            activebackground="#2dd4bf",
            activeforeground="#03221e",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self.start_stop_button.pack(fill="x", pady=(4, 8))

        self.start_minimized_var = tk.BooleanVar(value=False)
        self.start_minimized_check = tk.Checkbutton(
            panel,
            text="Start minimized",
            variable=self.start_minimized_var,
            command=self._on_start_minimized_changed,
            bg="#111827",
            fg="#d7e0ef",
            activebackground="#111827",
            activeforeground="#d7e0ef",
            selectcolor="#0f172a",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.start_minimized_check.pack(fill="x")

        self.start_with_windows_var = tk.BooleanVar(value=False)
        self.start_with_windows_check = tk.Checkbutton(
            panel,
            text="Start with Windows",
            variable=self.start_with_windows_var,
            command=self._on_start_with_windows_changed,
            bg="#111827",
            fg="#d7e0ef",
            activebackground="#111827",
            activeforeground="#d7e0ef",
            selectcolor="#0f172a",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.start_with_windows_check.pack(fill="x")

        self.start_monitoring_var = tk.BooleanVar(value=False)
        self.start_monitoring_check = tk.Checkbutton(
            panel,
            text="Start monitoring at launch",
            variable=self.start_monitoring_var,
            command=self._on_start_monitoring_changed,
            bg="#111827",
            fg="#d7e0ef",
            activebackground="#111827",
            activeforeground="#d7e0ef",
            selectcolor="#0f172a",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.start_monitoring_check.pack(fill="x")

        self.auto_minimize_var = tk.BooleanVar(value=False)
        self.auto_minimize_check = tk.Checkbutton(
            panel,
            text="Auto-minimize 5s after cursor hidden",
            variable=self.auto_minimize_var,
            command=self._on_auto_minimize_changed,
            bg="#111827",
            fg="#d7e0ef",
            activebackground="#111827",
            activeforeground="#d7e0ef",
            selectcolor="#0f172a",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.auto_minimize_check.pack(fill="x", pady=(0, 4))

        self.status_label = tk.Label(
            panel,
            text="Status: Stopped",
            bg="#0f172a",
            fg="#d7e0ef",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=10,
            pady=8,
            bd=0,
        )
        self.status_label.pack(fill="x", pady=(8, 0))

        self.timeout_var.trace_add("write", self._on_timeout_var_trace)

    def _apply_config_to_ui(self) -> None:
        try:
            self._config.start_with_windows = autostart.is_enabled(AUTOSTART_APP_NAME)
        except RuntimeError as exc:
            self._show_warning(str(exc))

        self.timeout_var.set(self._config.timeout_seconds)
        self.start_minimized_var.set(self._config.start_minimized)
        self.start_with_windows_var.set(self._config.start_with_windows)
        self.start_monitoring_var.set(self._config.start_monitoring_on_launch)
        self.auto_minimize_var.set(self._config.auto_minimize_on_hidden)
        self._save_config()

    def _toggle_monitoring(self) -> None:
        if self._monitor.running:
            self._monitor.stop()
            return
        self._monitor.start()

    def _on_running_changed(self, is_running: bool) -> None:
        self.start_stop_button.configure(text="Stop" if is_running else "Start")
        if is_running:
            self.start_stop_button.configure(bg="#ef4444", activebackground="#f87171", fg="#fff7f7")
        else:
            self.start_stop_button.configure(bg="#14b8a6", activebackground="#2dd4bf", fg="#03221e")

    def _on_timeout_var_trace(self, *_: object) -> None:
        self._on_timeout_changed()

    def _on_timeout_changed(self) -> None:
        try:
            value = int(self.timeout_var.get())
        except (tk.TclError, ValueError):
            return
        value = max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, value))
        if value != self.timeout_var.get():
            self.timeout_var.set(value)
            return
        self._monitor.set_timeout_seconds(value)
        if not self._loading_ui:
            self._config.timeout_seconds = value
            self._save_config()

    def _on_start_minimized_changed(self) -> None:
        if self._loading_ui:
            return
        self._config.start_minimized = bool(self.start_minimized_var.get())
        self._save_config()

    def _on_start_with_windows_changed(self) -> None:
        if self._loading_ui:
            return

        enabled = bool(self.start_with_windows_var.get())
        try:
            if enabled:
                autostart.enable(autostart.get_start_command(), AUTOSTART_APP_NAME)
            else:
                autostart.disable(AUTOSTART_APP_NAME)
        except RuntimeError as exc:
            self._show_error(str(exc))
            self.start_with_windows_var.set(not enabled)
            return

        self._config.start_with_windows = enabled
        self._save_config()

    def _on_start_monitoring_changed(self) -> None:
        if self._loading_ui:
            return
        self._config.start_monitoring_on_launch = bool(self.start_monitoring_var.get())
        self._save_config()

    def _on_auto_minimize_changed(self) -> None:
        if self._loading_ui:
            return
        enabled = bool(self.auto_minimize_var.get())
        self._config.auto_minimize_on_hidden = enabled
        if not enabled:
            self._cancel_auto_minimize_job()
        self._save_config()

    def _set_status(self, text: str) -> None:
        self._last_monitor_status = text
        self.status_label.configure(text=f"Status: {text}")

        if text == "Active":
            self.status_label.configure(bg="#07202b", fg="#67e8f9")
            self._cancel_auto_minimize_job()
        elif text == "Idle":
            self.status_label.configure(bg="#2b2110", fg="#fde68a")
            self._cancel_auto_minimize_job()
        elif text == "Cursor hidden":
            self.status_label.configure(bg="#2b1414", fg="#fecaca")
            self._schedule_auto_minimize()
        else:
            self.status_label.configure(bg="#0f172a", fg="#d7e0ef")
            self._cancel_auto_minimize_job()

    def _schedule_auto_minimize(self) -> None:
        self._cancel_auto_minimize_job()
        if not self.auto_minimize_var.get():
            return
        if self.root.state() == "iconic":
            return
        self._auto_minimize_job = self.root.after(AUTO_MINIMIZE_DELAY_MS, self._maybe_auto_minimize)

    def _cancel_auto_minimize_job(self) -> None:
        if self._auto_minimize_job is not None:
            self.root.after_cancel(self._auto_minimize_job)
            self._auto_minimize_job = None

    def _maybe_auto_minimize(self) -> None:
        self._auto_minimize_job = None
        if (
            self._config.auto_minimize_on_hidden
            and self._monitor.running
            and self._last_monitor_status == "Cursor hidden"
            and self.root.state() != "iconic"
        ):
            self.root.iconify()

    def _show_error(self, message: str) -> None:
        messagebox.showerror("Mouse Hider Lite - Error", message, parent=self.root)

    def _show_warning(self, message: str) -> None:
        messagebox.showwarning("Mouse Hider Lite - Warning", message, parent=self.root)

    def _save_config(self) -> None:
        try:
            self._config_manager.save(self._config)
        except OSError as exc:
            self._show_warning(f"Unable to save config.json: {exc}")

    def _on_close(self) -> None:
        self._config.timeout_seconds = int(self.timeout_var.get())
        self._config.start_minimized = bool(self.start_minimized_var.get())
        self._config.start_with_windows = bool(self.start_with_windows_var.get())
        self._config.start_monitoring_on_launch = bool(self.start_monitoring_var.get())
        self._config.auto_minimize_on_hidden = bool(self.auto_minimize_var.get())
        self._save_config()
        self._cancel_auto_minimize_job()
        self._monitor.stop()
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    app = MouseHiderLiteApp(root)
    if app._config.start_minimized:
        root.iconify()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
