"""Onboarding: get a device token from the control plane.

Two paths:
  * claim(code, relay_url)  — product flow: exchange a pairing code for a token.
  * auto_enroll(cp_url)     — POC flow: zero-config enroll over the tailnet
                             (the CP trusts the tailnet source; no code).
"""

from __future__ import annotations

import httpx

from .storage import AgentState, Storage


class OnboardError(RuntimeError):
    pass


def _apply(storage: Storage, state: AgentState, relay_url: str, data: dict) -> AgentState:
    state.device_id = data["device_id"]
    state.device_token = data["device_token"]
    state.relay_url = relay_url.rstrip("/")
    state.relay_ws_url = data["relay_ws_url"]
    storage.save(state)
    return state


def claim(storage: Storage, state: AgentState, *, code: str, relay_url: str, device_name: str) -> AgentState:
    relay_url = relay_url.rstrip("/")
    state.device_name = state.device_name or device_name
    try:
        resp = httpx.post(
            f"{relay_url}/api/pairing/claim",
            json={"code": code.strip().upper(), "device_name": state.device_name},
            timeout=15,
        )
    except httpx.HTTPError as exc:
        raise OnboardError(f"could not reach control plane at {relay_url}: {exc}") from exc
    if resp.status_code != 200:
        raise OnboardError(f"pairing failed ({resp.status_code}): {_detail(resp)}")
    return _apply(storage, state, relay_url, resp.json())


def auto_enroll(storage: Storage, state: AgentState, *, cp_url: str, device_name: str) -> AgentState:
    cp_url = cp_url.rstrip("/")
    state.device_name = state.device_name or device_name
    try:
        resp = httpx.post(f"{cp_url}/api/tailnet/enroll", json={"device_name": state.device_name}, timeout=15)
    except httpx.HTTPError as exc:
        raise OnboardError(f"could not reach control plane at {cp_url}: {exc}") from exc
    if resp.status_code != 200:
        raise OnboardError(f"tailnet enroll failed ({resp.status_code}): {_detail(resp)}")
    return _apply(storage, state, cp_url, resp.json())


def _detail(resp: httpx.Response) -> str:
    try:
        return resp.json().get("detail", resp.text)
    except ValueError:
        return resp.text
