"""System tray app — the end-user surface.

Double-clicking the installed app lands here (windowed, no console): an
always-visible tray icon that hosts the local dashboard and opens it in the
browser. This replaces the CLI as the product surface; the typer CLI stays
for dev/debug (`python -m agent ...`).
"""

from __future__ import annotations

import webbrowser

import pystray
from PIL import Image, ImageDraw

from .config import Settings
from .dashboard import serve


def _icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((6, 30, 58, 48), fill=(88, 166, 255, 255))   # saucer
    d.ellipse((22, 12, 42, 34), fill=(140, 210, 255, 255))  # dome
    return img


def main() -> None:
    settings = Settings()
    url = f"http://{settings.local_ui_host}:{settings.local_ui_port}"
    serve(settings.local_ui_host, settings.local_ui_port)

    def open_dashboard(icon, item):
        webbrowser.open(url)

    def quit_app(icon, item):
        icon.stop()

    icon = pystray.Icon(
        "ufo-agent",
        _icon_image(),
        "UFO Agent",
        menu=pystray.Menu(
            pystray.MenuItem("Open dashboard", open_dashboard, default=True),
            pystray.MenuItem("Quit", quit_app),
        ),
    )
    icon.run()


if __name__ == "__main__":
    main()
