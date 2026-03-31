from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_TIMEOUT_SECONDS = 10
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 300


@dataclass
class AppConfig:
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    start_minimized: bool = False
    start_with_windows: bool = False
    start_monitoring_on_launch: bool = False
    auto_minimize_on_hidden: bool = False


class ConfigManager:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            return AppConfig()

        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppConfig()

        config = AppConfig(
            timeout_seconds=self._sanitize_timeout(raw.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
            start_minimized=bool(raw.get("start_minimized", False)),
            start_with_windows=bool(raw.get("start_with_windows", False)),
            start_monitoring_on_launch=bool(raw.get("start_monitoring_on_launch", False)),
            auto_minimize_on_hidden=bool(raw.get("auto_minimize_on_hidden", False)),
        )
        return config

    def save(self, config: AppConfig) -> None:
        data = asdict(config)
        data["timeout_seconds"] = self._sanitize_timeout(data["timeout_seconds"])

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp_path.replace(self.config_path)

    @staticmethod
    def _sanitize_timeout(value: object) -> int:
        try:
            timeout = int(value)
        except (TypeError, ValueError):
            timeout = DEFAULT_TIMEOUT_SECONDS
        return max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, timeout))
