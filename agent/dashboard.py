"""Local dashboard (loopback-only) — the device owner's view.

Shows online/paired status + recent command output, and offers a manual
pairing fallback when tailnet auto-enroll isn't available. Loopback-only by
design: no auth, and it reflects a machine a remote AI can drive, so it must
never bind a public interface. Uses the stdlib HTTP server to keep the
windowed exe light.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import VERSION, Settings
from .identity import OnboardError, claim
from .runtime import AgentRuntime
from .storage import Storage

_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>UFO Agent</title><style>
 body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#0d1117;color:#c9d1d9;margin:0;padding:24px}
 .card{max-width:640px;margin:0 auto;background:#161b22;border:1px solid #21262d;border-radius:14px;padding:24px}
 h1{margin:0 0 4px;font-size:20px;color:#e6edf3} .v{color:#8b949e;font-size:13px}
 .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
 .on{background:#3fb950;box-shadow:0 0 6px #3fb95088}.off{background:#f85149}
 #out{margin-top:16px;max-height:340px;overflow-y:auto;background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:10px;font-family:ui-monospace,Menlo,monospace;font-size:12px;line-height:1.6}
 #out .t{color:#8b949e;margin-right:6px}#out .ty{color:#58a6ff;margin-right:6px}
 form{margin-top:16px;display:none;gap:8px}input{background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;padding:6px 10px}
 button{background:#238636;color:#fff;border:0;border-radius:6px;padding:6px 14px;cursor:pointer}
 .err{color:#f85149;font-size:12px}
</style></head><body><div class="card">
 <h1>🛸 UFO Agent</h1><div class="v" id="meta">loading…</div>
 <form id="pair"><input id="code" placeholder="ABCD-1234" size="12"><input id="relay" placeholder="http://host:8000" size="22"><button type="button" onclick="doPair()">Pair</button><span class="err" id="perr"></span></form>
 <div id="out"></div>
</div><script>
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function doPair(){$('#perr').textContent='';const r=await fetch('/api/pair',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:$('#code').value,relay_url:$('#relay').value})});if(!r.ok){$('#perr').textContent=(await r.json().catch(()=>({}))).detail||'failed';}refresh();}
async function refresh(){let s,ev;try{s=await (await fetch('/api/status')).json();ev=await (await fetch('/api/events')).json();}catch(e){$('#meta').textContent='agent not responding';return;}
 $('#meta').innerHTML=`v${esc(s.version)} · ${esc(s.device_name||'?')} · `+(s.online?'<span class="dot on"></span>online':'<span class="dot off"></span>offline')+(s.relay_url?' · '+esc(s.relay_url):'');
 $('#pair').style.display=s.paired?'none':'flex';
 if(!$('#relay').value&&s.control_plane_url)$('#relay').value=s.control_plane_url;
 const el=$('#out');const bot=el.scrollHeight-el.scrollTop-el.clientHeight<30;
 el.innerHTML=ev.slice(-150).map(e=>`<div><span class="t">${esc(e.ts)}</span><span class="ty">${esc(e.type)}</span>${esc(e.text)}</div>`).join('');
 if(bot)el.scrollTop=el.scrollHeight;}
refresh();setInterval(refresh,1500);
</script></body></html>"""


def make_server(runtime: AgentRuntime, storage: Storage, settings: Settings) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # silence
            pass

        def _send(self, body: bytes, ctype: str, code: int = 200) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(json.dumps(obj).encode(), "application/json", code)

        def do_GET(self):
            if self.path.startswith("/api/status"):
                state = storage.load()
                self._json({
                    "version": VERSION,
                    "device_name": state.device_name or settings.device_name,
                    "paired": state.paired,
                    "online": runtime.online,
                    "relay_url": runtime.relay_url or state.relay_url,
                    "control_plane_url": settings.control_plane_url,
                })
            elif self.path.startswith("/api/events"):
                self._json(list(runtime.recent))
            else:
                self._send(_PAGE.encode(), "text/html; charset=utf-8")

        def do_POST(self):
            if not self.path.startswith("/api/pair"):
                self._json({"detail": "not found"}, 404)
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                req = json.loads(self.rfile.read(length) or b"{}")
                relay_url = (req.get("relay_url") or "").strip() or settings.control_plane_url
                state = storage.load()
                claim(storage, state, code=req["code"], relay_url=relay_url, device_name=settings.device_name)
            except OnboardError as exc:
                self._json({"detail": str(exc)}, 400)
            except Exception as exc:
                self._json({"detail": f"{type(exc).__name__}: {exc}"}, 400)
            else:
                self._json({"ok": True})

    httpd = ThreadingHTTPServer((settings.local_ui_host, settings.local_ui_port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
