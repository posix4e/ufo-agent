"""Generate a multi-resolution icon.ico (a simple UFO mark) at build time.

Run in CI before PyInstaller/Inno Setup:  python packaging/make_icon.py packaging/icon.ico
"""

from __future__ import annotations

import sys

from PIL import Image, ImageDraw


def build(path: str) -> None:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((24, 120, 232, 184), fill=(88, 166, 255, 255))   # saucer
    d.ellipse((92, 48, 164, 132), fill=(140, 210, 255, 255))   # dome
    d.ellipse((104, 196, 120, 212), fill=(210, 153, 34, 255))  # light
    d.ellipse((168, 196, 184, 212), fill=(210, 153, 34, 255))  # light
    img.save(path, sizes=[(s, s) for s in (16, 32, 48, 64, 128, 256)])


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "icon.ico")
