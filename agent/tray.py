"""System tray app — the end-user surface.

The installed app lands here (windowed, no console): an always-visible tray
icon that hosts the local dashboard and runs the relay client (which auto-pairs
on the tailnet and executes commands from the control plane).
"""

from __future__ import annotations

import asyncio
import threading
import webbrowser

import pystray
from PIL import Image, ImageDraw

from .config import Settings
from .dashboard import make_server
from .relay_client import RelayClient
from .runtime import AgentRuntime
from .storage import Storage


def _icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((6, 30, 58, 48), fill=(88, 166, 255, 255))    # saucer
    d.ellipse((22, 12, 42, 34), fill=(140, 210, 255, 255))  # dome
    return img


def _run_relay(settings: Settings, storage: Storage, runtime: AgentRuntime) -> None:
    asyncio.run(RelayClient(settings, storage, runtime).run())


def main() -> None:
    settings = Settings()
    storage = Storage()
    runtime = AgentRuntime()

    make_server(runtime, storage, settings)
    threading.Thread(target=_run_relay, args=(settings, storage, runtime), daemon=True).start()

    url = f"http://{settings.local_ui_host}:{settings.local_ui_port}"
    icon = pystray.Icon(
        "ufo-agent",
        _icon_image(),
        "UFO Agent",
        menu=pystray.Menu(
            pystray.MenuItem("Open dashboard", lambda icon, item: webbrowser.open(url), default=True),
            pystray.MenuItem("Quit", lambda icon, item: icon.stop()),
        ),
    )
    icon.run()


if __name__ == "__main__":
    main()
