"""Minimal local dashboard, served on loopback (skeleton).

Grows into the pairing / status / approve-deny UI. Loopback-only by design:
no auth, and it will eventually approve actions, so it must never bind a
public interface. Uses the stdlib HTTP server to keep the windowed exe light.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import VERSION, Settings

_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>UFO Agent</title>
<style>
 body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#0d1117;color:#c9d1d9;
   display:grid;place-items:center;height:100vh;margin:0}}
 .card{{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:30px 40px;text-align:center}}
 h1{{margin:0 0 6px;font-size:22px;color:#e6edf3}} .v{{color:#8b949e;font-size:13px}}
 .s{{margin-top:16px;color:#d29922;font-size:14px}}
</style></head><body><div class="card">
 <h1>🛸 UFO Agent</h1>
 <div class="v">v{version} · {device}</div>
 <div class="s">Not paired yet — pairing UI coming soon.</div>
</div></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence default stderr logging
        pass

    def do_GET(self):
        settings = Settings()
        if self.path.startswith("/api/status"):
            body = json.dumps(
                {"version": VERSION, "device_name": settings.device_name, "paired": False}
            ).encode()
            ctype = "application/json"
        else:
            body = _PAGE.format(version=VERSION, device=settings.device_name).encode()
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str, port: int) -> ThreadingHTTPServer:
    """Start the dashboard in a background thread; return the server."""
    httpd = ThreadingHTTPServer((host, port), _Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
