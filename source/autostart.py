from __future__ import annotations

import sys
from pathlib import Path
import winreg


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "MouseHider"


def get_start_command() -> str:
    if getattr(sys, "frozen", False):
        return _quote(Path(sys.executable))

    python_path = Path(sys.executable)
    pythonw_path = python_path.with_name("pythonw.exe")
    interpreter = pythonw_path if pythonw_path.exists() else python_path
    script_path = Path(sys.argv[0]).resolve()
    return f"{_quote(interpreter)} {_quote(script_path)}"


def is_enabled(app_name: str = APP_NAME) -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, app_name)
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise RuntimeError(f"Unable to read startup registry key: {exc}") from exc


def enable(command: str, app_name: str = APP_NAME) -> None:
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
    except OSError as exc:
        raise RuntimeError(f"Unable to enable startup with Windows: {exc}") from exc


def disable(app_name: str = APP_NAME) -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, app_name)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise RuntimeError(f"Unable to disable startup with Windows: {exc}") from exc


def _quote(path: Path) -> str:
    return f'"{path}"'
