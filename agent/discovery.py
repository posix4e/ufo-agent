"""Discover the control plane on the tailnet — POC zero-config onboarding.

Runs ``tailscale status --json`` (local API, no key needed), then probes each
peer's ``:8000/healthz`` to find the one running ufo-control-plane. No tags or
renaming needed — the CP is identified by the service it serves. Returns None
when Tailscale isn't present or no CP is found (the agent then falls back to
manual pairing).
"""

from __future__ import annotations

import json
import shutil
import subprocess

import httpx

CP_PORT = 8000
HEALTH_PATH = "/healthz"
CP_SERVICE = "ufo-control-plane"


def _tailscale_status() -> dict | None:
    exe = shutil.which("tailscale")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "status", "--json"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except ValueError:
        return None


def self_name(status: dict | None = None) -> str | None:
    status = status or _tailscale_status()
    if not status:
        return None
    return (status.get("Self") or {}).get("HostName")


def _peer_addresses(status: dict) -> list[str]:
    addrs: list[str] = []
    for peer in (status.get("Peer") or {}).values():
        for ip in peer.get("TailscaleIPs") or []:
            if ":" not in ip:  # IPv4 only (simpler URLs)
                addrs.append(ip)
    return addrs


def discover_cp() -> str | None:
    """Return the base URL of the control plane on the tailnet, or None."""
    status = _tailscale_status()
    if not status:
        return None
    for ip in _peer_addresses(status):
        url = f"http://{ip}:{CP_PORT}"
        try:
            resp = httpx.get(f"{url}{HEALTH_PATH}", timeout=3)
            if resp.status_code == 200 and resp.json().get("service") == CP_SERVICE:
                return url
        except (httpx.HTTPError, ValueError):
            continue
    return None
