"""Local persistent state for the agent (pairing identity + token).

Targets Windows first (``%LOCALAPPDATA%\\UFO Agent``) but works cross-platform
so the agent can be developed on macOS/Linux.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from pydantic import BaseModel

APP_DIR_NAME = "UFO Agent"


def default_data_dir() -> Path:
    override = os.environ.get("UFO_AGENT_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return base / APP_DIR_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return base / "ufo-agent"


class AgentState(BaseModel):
    install_id: str | None = None
    device_id: str | None = None
    device_token: str | None = None
    device_name: str | None = None
    relay_url: str | None = None  # control plane base URL
    relay_ws_url: str | None = None  # device WebSocket URL

    @property
    def paired(self) -> bool:
        return bool(self.device_token and self.relay_ws_url)


class Storage:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.data_dir / "state.json"

    def load(self) -> AgentState:
        if self.state_path.exists():
            return AgentState.model_validate_json(self.state_path.read_text(encoding="utf-8"))
        return AgentState(install_id=str(uuid.uuid4()))

    def save(self, state: AgentState) -> None:
        # Contains the device token in plaintext (per-user dir). Protect with
        # DPAPI / Credential Manager before production.
        self.state_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
