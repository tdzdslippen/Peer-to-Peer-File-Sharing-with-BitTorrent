from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Any

from rich.console import Console


class EventLogger:
    def __init__(self) -> None:
        self.console = Console()
        self._lock = Lock()

    def info(self, event: str, **fields: Any) -> None:
        self._log("INFO", "green", event, **fields)

    def warn(self, event: str, **fields: Any) -> None:
        self._log("WARN", "yellow", event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self._log("ERROR", "red", event, **fields)

    def _log(self, level: str, color: str, event: str, **fields: Any) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        details = " ".join(f"{key}={value}" for key, value in fields.items())
        text = f"[{color}]{timestamp} {level:<5} {event}[/{color}]"
        if details:
            text = f"{text} {details}"
        with self._lock:
            self.console.print(text)
