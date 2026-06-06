"""Run a shell command on this machine, streaming output line by line.

The remote-exec capability: the control plane sends a command, this runs it on
the box (default shell — cmd on Windows, /bin/sh elsewhere) and streams stdout
+ stderr back through ``on_line``. Effectively a remote shell — see the safety
notes in the README; only the paired control plane can reach it.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

LineCallback = Callable[[str], Awaitable[None]]


async def run_command(command: str, on_line: LineCallback, *, timeout: float = 600.0) -> int:
    """Run ``command`` in the default shell; stream combined output; return exit code."""
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    async def pump() -> None:
        assert proc.stdout is not None
        async for raw in proc.stdout:
            await on_line(raw.decode(errors="replace").rstrip("\r\n"))

    try:
        await asyncio.wait_for(pump(), timeout=timeout)
        return await proc.wait()
    except asyncio.TimeoutError:
        proc.kill()
        await on_line(f"[killed: exceeded {timeout:.0f}s timeout]")
        return 124
