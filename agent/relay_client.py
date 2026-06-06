"""Outbound WebSocket client to the control plane.

The device dials OUT only (no inbound ports). Reconnects with backoff; when not
yet paired it tries tailnet auto-discovery + enroll (POC), else waits for manual
pairing. Handles ``run_task`` (type ``exec`` runs a shell command and streams
output back as ``task_log`` + ``task_completed``).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import websockets
from rich.console import Console

from .config import VERSION, Settings
from .discovery import discover_cp, self_name
from .executor import run_command
from .identity import OnboardError, auto_enroll
from .protocol import DeviceMsg, RelayMsg
from .runtime import AgentRuntime
from .storage import Storage

console = Console()
MAX_FRAME_BYTES = 10 * 1024 * 1024


class RelayClient:
    def __init__(self, settings: Settings, storage: Storage, runtime: AgentRuntime) -> None:
        self.settings = settings
        self.storage = storage
        self.runtime = runtime
        self.state = storage.load()
        self._ws: websockets.WebSocketClientProtocol | None = None

    # --- onboarding -------------------------------------------------------------

    def _try_onboard(self) -> bool:
        """Reload pairing from disk; if still unpaired, try tailnet auto-enroll."""
        self.state = self.storage.load()
        if self.state.paired:
            return True
        if not self.settings.tailnet_autopair:
            return False
        cp_url = discover_cp()
        if not cp_url:
            return False
        name = self.state.device_name or self_name() or self.settings.device_name
        try:
            self.state = auto_enroll(self.storage, self.state, cp_url=cp_url, device_name=name)
            console.log(f"[green]auto-enrolled on the tailnet via[/green] {cp_url}")
            return True
        except OnboardError as exc:
            console.log(f"[yellow]auto-enroll failed: {exc}[/yellow]")
            return False

    # --- send -------------------------------------------------------------------

    async def send(self, type_: str, payload: dict[str, Any]) -> None:
        ws = self._ws
        if ws is None:
            return
        try:
            await ws.send(json.dumps({"type": type_, "payload": payload}, default=str))
        except Exception as exc:
            console.log(f"[yellow]send failed: {exc}[/yellow]")

    async def _send_status(self) -> None:
        await self.send(
            DeviceMsg.STATUS,
            {"version": VERSION, "device_name": self.state.device_name, "paired": True},
        )

    # --- connection loop --------------------------------------------------------

    async def run(self) -> None:
        backoff = self.settings.reconnect_min_seconds
        while True:
            if not self._try_onboard():
                await asyncio.sleep(3.0)
                continue

            url = f"{self.state.relay_ws_url}?token={self.state.device_token}"
            self.runtime.relay_url = self.state.relay_url
            try:
                async with websockets.connect(url, max_size=MAX_FRAME_BYTES) as ws:
                    self._ws = ws
                    self.runtime.online = True
                    backoff = self.settings.reconnect_min_seconds
                    console.log(f"[green]connected to control plane:[/green] {self.state.relay_url}")
                    self.runtime.event("connected", self.state.relay_url or "")
                    await self.send(DeviceMsg.HELLO, {"version": VERSION, "device_name": self.state.device_name})
                    await self._send_status()
                    hb = asyncio.create_task(self._heartbeat())
                    try:
                        async for raw in ws:
                            await self._handle(raw)
                    finally:
                        hb.cancel()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                console.log(f"[yellow]connection error: {exc}[/yellow]")
            finally:
                self._ws = None
                self.runtime.online = False

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self.settings.reconnect_max_seconds)

    async def _heartbeat(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.settings.heartbeat_seconds)
                await self._send_status()
        except asyncio.CancelledError:
            pass

    # --- inbound ----------------------------------------------------------------

    async def _handle(self, raw: str | bytes) -> None:
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return
        mtype = msg.get("type")
        payload = msg.get("payload") or {}
        if mtype == RelayMsg.RUN_TASK:
            asyncio.create_task(self._run_task(payload))
        elif mtype == RelayMsg.DISCONNECT:
            if self._ws is not None:
                await self._ws.close()

    async def _run_task(self, task: dict[str, Any]) -> None:
        task_id = str(task.get("task_id", ""))
        ttype = task.get("type", "run_instruction")
        instruction = str(task.get("instruction", ""))

        if ttype != "exec":
            await self.send(
                DeviceMsg.TASK_FAILED,
                {"task_id": task_id, "summary": f"unsupported task type '{ttype}' (only 'exec' so far)"},
            )
            return

        await self.send(DeviceMsg.TASK_STARTED, {"task_id": task_id, "instruction": instruction})
        self.runtime.event("exec", instruction)

        async def on_line(line: str) -> None:
            await self.send(DeviceMsg.TASK_LOG, {"task_id": task_id, "line": line})
            self.runtime.event("output", line)

        try:
            exit_code = await run_command(instruction, on_line)
        except Exception as exc:
            await self.send(DeviceMsg.TASK_FAILED, {"task_id": task_id, "summary": f"{type(exc).__name__}: {exc}"})
            return
        await self.send(
            DeviceMsg.TASK_COMPLETED,
            {"task_id": task_id, "exit_code": exit_code, "summary": f"exit {exit_code}"},
        )
        self.runtime.event("done", f"exit {exit_code}")
