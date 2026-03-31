from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QCloseEvent, QColor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import autostart
from config_manager import ConfigManager, DEFAULT_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS, MIN_TIMEOUT_SECONDS
from cursor_monitor import MouseInactivityMonitor


AUTOSTART_APP_NAME = "MouseHider64"


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


class MouseHiderWindow(QMainWindow):
    AUTO_MINIMIZE_DELAY_MS = 5000

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HPE - Mouse Hider")
        self.setMinimumWidth(420)
        self.setWindowIcon(self._create_mouse_icon())

        self._config_manager = ConfigManager(get_app_dir() / "config.json")
        self._config = self._config_manager.load()
        self._loading_ui = True

        self._monitor = MouseInactivityMonitor(timeout_seconds=self._config.timeout_seconds)
        self._monitor.status_changed.connect(self._set_status)
        self._monitor.error_occurred.connect(self._on_monitor_error)
        self._monitor.running_changed.connect(self._on_running_changed)

        self._last_monitor_status = "Stopped"
        self._auto_minimize_timer = QTimer(self)
        self._auto_minimize_timer.setSingleShot(True)
        self._auto_minimize_timer.timeout.connect(self._maybe_auto_minimize)

        self._build_ui()
        self._apply_config_to_ui()
        self._loading_ui = False

        self._set_status("Stopped")
        if self._config.start_monitoring_on_launch:
            self._monitor.start()

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(0)

        panel = QWidget(self)
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(12)

        title_label = QLabel("Mouse Hider", self)
        title_label.setObjectName("titleLabel")
        panel_layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        self.timeout_spin = QSpinBox(self)
        self.timeout_spin.setRange(MIN_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.setValue(DEFAULT_TIMEOUT_SECONDS)
        self.timeout_spin.setFixedWidth(110)
        self.timeout_spin.valueChanged.connect(self._on_timeout_changed)
        form_layout.addRow("Idle timeout:", self.timeout_spin)

        panel_layout.addLayout(form_layout)

        self.start_stop_button = QPushButton("Start", self)
        self.start_stop_button.setCursor(Qt.PointingHandCursor)
        self.start_stop_button.setProperty("running", False)
        self.start_stop_button.clicked.connect(self._toggle_monitoring)

        button_row = QHBoxLayout()
        button_row.addWidget(self.start_stop_button)
        panel_layout.addLayout(button_row)

        self.start_minimized_checkbox = QCheckBox("Start minimized", self)
        self.start_minimized_checkbox.stateChanged.connect(self._on_start_minimized_changed)
        panel_layout.addWidget(self.start_minimized_checkbox)

        self.start_with_windows_checkbox = QCheckBox("Start with Windows", self)
        self.start_with_windows_checkbox.stateChanged.connect(self._on_start_with_windows_changed)
        panel_layout.addWidget(self.start_with_windows_checkbox)

        self.start_monitoring_checkbox = QCheckBox("Start monitoring at launch", self)
        self.start_monitoring_checkbox.stateChanged.connect(self._on_start_monitoring_on_launch_changed)
        panel_layout.addWidget(self.start_monitoring_checkbox)

        self.auto_minimize_checkbox = QCheckBox("Auto-minimize 5s after cursor hidden", self)
        self.auto_minimize_checkbox.stateChanged.connect(self._on_auto_minimize_changed)
        panel_layout.addWidget(self.auto_minimize_checkbox)

        self.status_label = QLabel("Stopped", self)
        self.status_label.setObjectName("statusLabel")
        panel_layout.addWidget(self.status_label)

        root_layout.addWidget(panel)
        root_layout.addStretch(1)
        self.setCentralWidget(central_widget)
        self._apply_style()

    def _apply_style(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setFont(QFont("Segoe UI", 10))
            app.setStyle("Fusion")
            app.setPalette(self._build_dark_palette())

        self.setStyleSheet(
            """
            QWidget#centralWidget {
                background-color: #0b1220;
            }
            QWidget#panel {
                background-color: #111827;
                border: 1px solid #273449;
                border-radius: 14px;
            }
            QLabel {
                color: #d7e0ef;
            }
            QLabel#titleLabel {
                font-size: 15px;
                font-weight: 600;
                color: #f8fafc;
            }
            QSpinBox {
                min-height: 28px;
                border: 1px solid #3c4d66;
                border-radius: 7px;
                padding: 0 8px;
                background-color: #0f172a;
                color: #f8fafc;
                selection-background-color: #22d3ee;
                selection-color: #06131c;
            }
            QSpinBox:focus {
                border: 1px solid #22d3ee;
            }
            QCheckBox {
                spacing: 8px;
                color: #d7e0ef;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #60708a;
                background: #0f172a;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #14b8a6;
                background: #14b8a6;
            }
            QPushButton {
                min-height: 34px;
                border: 0;
                border-radius: 8px;
                font-weight: 600;
                background-color: #14b8a6;
                color: #03221e;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #2dd4bf;
            }
            QPushButton:pressed {
                background-color: #0d9488;
            }
            QPushButton[running="true"] {
                background-color: #ef4444;
                color: #fff7f7;
            }
            QPushButton[running="true"]:hover {
                background-color: #f87171;
            }
            QPushButton[running="true"]:pressed {
                background-color: #dc2626;
            }
            QLabel#statusLabel {
                margin-top: 4px;
                border: 1px solid #334155;
                border-radius: 8px;
                background-color: #0f172a;
                padding: 8px 10px;
                font-weight: 600;
                color: #cbd5e1;
            }
            QLabel#statusLabel[state="active"] {
                color: #67e8f9;
                border-color: #0e7490;
                background-color: #07202b;
            }
            QLabel#statusLabel[state="idle"] {
                color: #fde68a;
                border-color: #854d0e;
                background-color: #2b2110;
            }
            QLabel#statusLabel[state="hidden"] {
                color: #fecaca;
                border-color: #7f1d1d;
                background-color: #2b1414;
            }
            QLabel#statusLabel[state="stopped"] {
                color: #d7e0ef;
                border-color: #334155;
                background-color: #0f172a;
            }
            """
        )

    @staticmethod
    def _build_dark_palette() -> QPalette:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#0b1220"))
        palette.setColor(QPalette.WindowText, QColor("#d7e0ef"))
        palette.setColor(QPalette.Base, QColor("#0f172a"))
        palette.setColor(QPalette.AlternateBase, QColor("#111827"))
        palette.setColor(QPalette.ToolTipBase, QColor("#111827"))
        palette.setColor(QPalette.ToolTipText, QColor("#e5edf8"))
        palette.setColor(QPalette.Text, QColor("#e5edf8"))
        palette.setColor(QPalette.Button, QColor("#111827"))
        palette.setColor(QPalette.ButtonText, QColor("#d7e0ef"))
        palette.setColor(QPalette.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.Highlight, QColor("#22d3ee"))
        palette.setColor(QPalette.HighlightedText, QColor("#06131c"))
        return palette

    @staticmethod
    def _create_mouse_icon(size: int = 64) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        body_color = QColor("#14b8a6")
        stroke_color = QColor("#0f172a")
        wheel_color = QColor("#0f172a")

        margin = int(size * 0.18)
        width = size - (margin * 2)
        height = int(size * 0.70)
        x = margin
        y = int(size * 0.14)

        painter.setPen(QPen(stroke_color, max(2, size // 16)))
        painter.setBrush(QBrush(body_color))
        painter.drawRoundedRect(x, y, width, height, width * 0.45, width * 0.45)

        split_y = y + int(height * 0.33)
        painter.setPen(QPen(stroke_color, max(2, size // 24)))
        painter.drawLine(x + int(width * 0.5), y + int(height * 0.06), x + int(width * 0.5), split_y)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(wheel_color))
        wheel_w = max(3, size // 10)
        wheel_h = max(6, size // 8)
        wheel_x = x + (width // 2) - (wheel_w // 2)
        wheel_y = y + int(height * 0.16)
        painter.drawRoundedRect(wheel_x, wheel_y, wheel_w, wheel_h, wheel_w * 0.4, wheel_w * 0.4)

        painter.end()
        return QIcon(pixmap)

    def _apply_config_to_ui(self) -> None:
        # Reflect actual startup registry state at launch.
        try:
            self._config.start_with_windows = autostart.is_enabled(AUTOSTART_APP_NAME)
        except RuntimeError as exc:
            self._show_warning(str(exc))

        self.timeout_spin.setValue(self._config.timeout_seconds)
        self.start_minimized_checkbox.setChecked(self._config.start_minimized)
        self.start_with_windows_checkbox.setChecked(self._config.start_with_windows)
        self.start_monitoring_checkbox.setChecked(self._config.start_monitoring_on_launch)
        self.auto_minimize_checkbox.setChecked(self._config.auto_minimize_on_hidden)
        self._save_config()

    def _toggle_monitoring(self) -> None:
        if self._monitor.running:
            self._monitor.stop()
            return
        self._monitor.start()

    def _on_running_changed(self, is_running: bool) -> None:
        self.start_stop_button.setText("Stop" if is_running else "Start")
        self.start_stop_button.setProperty("running", is_running)
        self._refresh_widget_style(self.start_stop_button)

    def _on_timeout_changed(self, value: int) -> None:
        self._monitor.set_timeout_seconds(value)
        if not self._loading_ui:
            self._config.timeout_seconds = value
            self._save_config()

    def _on_start_minimized_changed(self, state: int) -> None:
        if self._loading_ui:
            return
        self._config.start_minimized = state == Qt.Checked
        self._save_config()

    def _on_start_with_windows_changed(self, state: int) -> None:
        if self._loading_ui:
            return

        enabled = state == Qt.Checked
        try:
            if enabled:
                autostart.enable(autostart.get_start_command(), AUTOSTART_APP_NAME)
            else:
                autostart.disable(AUTOSTART_APP_NAME)
        except RuntimeError as exc:
            self._show_error(str(exc))
            self.start_with_windows_checkbox.blockSignals(True)
            self.start_with_windows_checkbox.setChecked(not enabled)
            self.start_with_windows_checkbox.blockSignals(False)
            return

        self._config.start_with_windows = enabled
        self._save_config()

    def _on_start_monitoring_on_launch_changed(self, state: int) -> None:
        if self._loading_ui:
            return
        self._config.start_monitoring_on_launch = state == Qt.Checked
        self._save_config()

    def _on_auto_minimize_changed(self, state: int) -> None:
        if self._loading_ui:
            return
        enabled = state == Qt.Checked
        self._config.auto_minimize_on_hidden = enabled
        if not enabled:
            self._auto_minimize_timer.stop()
        self._save_config()

    def _on_monitor_error(self, message: str) -> None:
        self._show_error(message)

    def _set_status(self, text: str) -> None:
        self._last_monitor_status = text
        state = "stopped"
        if text == "Active":
            state = "active"
        elif text == "Idle":
            state = "idle"
        elif text == "Cursor hidden":
            state = "hidden"
            if self.auto_minimize_checkbox.isChecked() and self.isVisible() and not self.isMinimized():
                self._auto_minimize_timer.start(self.AUTO_MINIMIZE_DELAY_MS)
        else:
            self._auto_minimize_timer.stop()

        if text != "Cursor hidden":
            self._auto_minimize_timer.stop()

        self.status_label.setProperty("state", state)
        self._refresh_widget_style(self.status_label)
        self.status_label.setText(f"Status: {text}")

    def _maybe_auto_minimize(self) -> None:
        if (
            self._config.auto_minimize_on_hidden
            and self._monitor.running
            and self._last_monitor_status == "Cursor hidden"
            and self.isVisible()
            and not self.isMinimized()
        ):
            self.showMinimized()

    def _save_config(self) -> None:
        try:
            self._config_manager.save(self._config)
        except OSError as exc:
            self._show_warning(f"Unable to save config.json: {exc}")

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Mouse Hider - Error", message)

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "Mouse Hider - Warning", message)

    @staticmethod
    def _refresh_widget_style(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._config.timeout_seconds = self.timeout_spin.value()
        self._config.start_minimized = self.start_minimized_checkbox.isChecked()
        self._config.start_with_windows = self.start_with_windows_checkbox.isChecked()
        self._config.start_monitoring_on_launch = self.start_monitoring_checkbox.isChecked()
        self._config.auto_minimize_on_hidden = self.auto_minimize_checkbox.isChecked()
        self._save_config()
        self._auto_minimize_timer.stop()
        self._monitor.stop()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setWindowIcon(MouseHiderWindow._create_mouse_icon())
    window = MouseHiderWindow()
    if window._config.start_minimized:
        window.showMinimized()
    else:
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
