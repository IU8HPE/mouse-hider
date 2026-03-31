from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

from PySide6.QtCore import QObject, QTimer, Signal

from config_manager import DEFAULT_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS, MIN_TIMEOUT_SECONDS


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", POINT),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)

GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
GetCursorPos.restype = wintypes.BOOL

ShowCursor = user32.ShowCursor
ShowCursor.argtypes = [wintypes.BOOL]
ShowCursor.restype = ctypes.c_int

CreateCursor = user32.CreateCursor
CreateCursor.argtypes = [
    wintypes.HINSTANCE,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
]
CreateCursor.restype = wintypes.HANDLE

SetSystemCursor = user32.SetSystemCursor
SetSystemCursor.argtypes = [wintypes.HANDLE, wintypes.DWORD]
SetSystemCursor.restype = wintypes.BOOL

DestroyCursor = user32.DestroyCursor
DestroyCursor.argtypes = [wintypes.HANDLE]
DestroyCursor.restype = wintypes.BOOL

SystemParametersInfoW = user32.SystemParametersInfoW
SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
SystemParametersInfoW.restype = wintypes.BOOL


SPI_SETCURSORS = 0x0057
CURSOR_WIDTH = 32
CURSOR_HEIGHT = 32
SYSTEM_CURSOR_IDS = (
    32512,  # OCR_NORMAL
    32513,  # OCR_IBEAM
    32514,  # OCR_WAIT
    32515,  # OCR_CROSS
    32516,  # OCR_UP
    32642,  # OCR_SIZENWSE
    32643,  # OCR_SIZENESW
    32644,  # OCR_SIZEWE
    32645,  # OCR_SIZENS
    32646,  # OCR_SIZEALL
    32648,  # OCR_NO
    32649,  # OCR_HAND
    32650,  # OCR_APPSTARTING
    32651,  # OCR_HELP
)


class MouseInactivityMonitor(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)
    running_changed = Signal(bool)

    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, poll_interval_ms: int = 100) -> None:
        super().__init__()
        self._timeout_seconds = self._clamp_timeout(timeout_seconds)
        self._poll_interval_ms = max(20, int(poll_interval_ms))
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_mouse)

        self._last_pos: tuple[int, int] | None = None
        self._last_move_ts = time.monotonic()
        self._cursor_hidden = False
        self._hide_mode = "none"
        self._running = False
        self._last_status = ""

    @property
    def running(self) -> bool:
        return self._running

    @property
    def timeout_seconds(self) -> int:
        return self._timeout_seconds

    def set_timeout_seconds(self, timeout_seconds: int) -> None:
        self._timeout_seconds = self._clamp_timeout(timeout_seconds)
        if not self._running:
            return

        idle_seconds = time.monotonic() - self._last_move_ts
        if self._cursor_hidden and idle_seconds < self._timeout_seconds:
            try:
                self._ensure_cursor_visible()
            except RuntimeError as exc:
                self.error_occurred.emit(str(exc))
                self.stop()
                return
            self._emit_status("Idle")
        elif self._cursor_hidden:
            self._emit_status("Cursor hidden")
        else:
            self._emit_status("Active")

    def start(self) -> None:
        if self._running:
            return
        try:
            self._last_pos = self._get_cursor_pos()
        except RuntimeError as exc:
            self.error_occurred.emit(str(exc))
            return

        self._last_move_ts = time.monotonic()
        self._running = True
        self._timer.start(self._poll_interval_ms)
        self.running_changed.emit(True)
        self._emit_status("Active")

    def stop(self) -> None:
        if not self._running:
            self._safe_restore_cursor()
            self._emit_status("Stopped")
            return

        self._timer.stop()
        self._running = False
        self._safe_restore_cursor()
        self.running_changed.emit(False)
        self._emit_status("Stopped")

    def _poll_mouse(self) -> None:
        try:
            pos = self._get_cursor_pos()
            now = time.monotonic()
            if self._last_pos is None or pos != self._last_pos:
                self._last_pos = pos
                self._last_move_ts = now
                if self._cursor_hidden:
                    self._ensure_cursor_visible()
                self._emit_status("Active")
                return

            idle_seconds = now - self._last_move_ts
            if idle_seconds >= self._timeout_seconds:
                if not self._cursor_hidden:
                    self._ensure_cursor_hidden()
                self._emit_status("Cursor hidden")
            else:
                self._emit_status("Idle")
        except RuntimeError as exc:
            self.error_occurred.emit(str(exc))
            self.stop()

    def _ensure_cursor_hidden(self) -> None:
        if self._cursor_hidden:
            return
        system_error: RuntimeError | None = None
        try:
            self._hide_cursor_systemwide()
            self._hide_mode = "system"
            self._cursor_hidden = True
            return
        except RuntimeError as exc:
            system_error = exc

        guard = 0
        while ShowCursor(False) >= 0:
            guard += 1
            if guard > 128:
                if system_error is not None:
                    raise RuntimeError(f"{system_error} (ShowCursor fallback failed).")
                raise RuntimeError("Unable to hide cursor reliably.")
        self._hide_mode = "showcursor"
        self._cursor_hidden = True

    def _ensure_cursor_visible(self) -> None:
        if not self._cursor_hidden:
            return

        if self._hide_mode == "system":
            if not SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0):
                err = ctypes.get_last_error()
                raise RuntimeError(f"Unable to restore system cursors: {ctypes.FormatError(err)}")
        else:
            guard = 0
            while ShowCursor(True) < 0:
                guard += 1
                if guard > 128:
                    raise RuntimeError("Unable to restore cursor reliably.")

        self._cursor_hidden = False
        self._hide_mode = "none"

    @staticmethod
    def _hide_cursor_systemwide() -> None:
        mask_size = (CURSOR_WIDTH * CURSOR_HEIGHT) // 8
        and_plane = (ctypes.c_ubyte * mask_size)(*([0xFF] * mask_size))
        xor_plane = (ctypes.c_ubyte * mask_size)(*([0x00] * mask_size))

        and_ptr = ctypes.cast(and_plane, ctypes.c_void_p)
        xor_ptr = ctypes.cast(xor_plane, ctypes.c_void_p)

        for cursor_id in SYSTEM_CURSOR_IDS:
            cursor_handle = CreateCursor(
                None,
                0,
                0,
                CURSOR_WIDTH,
                CURSOR_HEIGHT,
                and_ptr,
                xor_ptr,
            )
            if not cursor_handle:
                err = ctypes.get_last_error()
                raise RuntimeError(f"Unable to create transparent cursor: {ctypes.FormatError(err)}")

            if not SetSystemCursor(cursor_handle, cursor_id):
                err = ctypes.get_last_error()
                DestroyCursor(cursor_handle)
                raise RuntimeError(f"Unable to hide system cursor: {ctypes.FormatError(err)}")

    def _emit_status(self, text: str) -> None:
        if text == self._last_status:
            return
        self._last_status = text
        self.status_changed.emit(text)

    def _safe_restore_cursor(self) -> None:
        try:
            self._ensure_cursor_visible()
        except RuntimeError as exc:
            self.error_occurred.emit(str(exc))

    @staticmethod
    def _get_cursor_pos() -> tuple[int, int]:
        point = POINT()
        if not GetCursorPos(ctypes.byref(point)):
            err = ctypes.get_last_error()
            raise RuntimeError(f"WinAPI GetCursorPos failed: {ctypes.FormatError(err)}")
        return point.x, point.y

    @staticmethod
    def _clamp_timeout(value: int) -> int:
        try:
            timeout = int(value)
        except (TypeError, ValueError):
            timeout = DEFAULT_TIMEOUT_SECONDS
        return max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, timeout))
