"""Shared runtime state between the relay client and the local dashboard."""

from __future__ import annotations

import time
from collections import deque
from typing import Any


class AgentRuntime:
    def __init__(self, maxlen: int = 200) -> None:
        self.online = False
        self.relay_url: str | None = None
        self.recent: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def event(self, type_: str, text: str = "") -> None:
        self.recent.append({"ts": time.strftime("%H:%M:%S"), "type": type_, "text": text})
