# ufo-agent

**Install once. Pair your PC. Let your AI use this Windows machine — safely.**

A Windows device agent that pairs a PC to a [**ufo-control-plane**](https://github.com/posix4e/ufo-control-plane)
and lets a remote AI drive it, with local approval and always-visible activity.

➡️ **Download the installer:** https://posix4e.github.io/ufo-agent

> **Status: skeleton.** A CLI and clean structure today; pairing, the outbound
> relay client, the GUI automation backend (eventually Microsoft UFO²), policy,
> approvals, and the local UI are being built deliberately. Reference POC:
> [ufo-device-agent](https://github.com/posix4e/ufo-device-agent).

## Principles (carried from the prototype)

- **Outbound only** — the device dials out to the control plane. No inbound
  ports, no RDP, no VPN.
- **Real actions or honest failure** — no mocks, no simulation.
- **Always visible & locally controllable** — pause / approve / deny from a
  local UI; no stealth mode, ever.

## Install (end user)

Visit **https://posix4e.github.io/ufo-agent** and download `ufo-agent.exe`
(built and published straight from CI). No Python required. *(Unsigned for now —
expect a SmartScreen prompt; code-signing is on the roadmap.)*

## Run (dev)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m agent version
python -m agent status
```

## Layout

```
agent/        CLI (cli), config (pairing / relay / automation / ui grow here)
packaging/    PyInstaller entry point for ufo-agent.exe
web/          GitHub Pages download page
tests/        pytest
```

## Roadmap

1. **Identity + pairing** — claim a code → store a device token
2. **Outbound WebSocket client** to the control plane
3. **Automation backend** — native Windows actions → Microsoft UFO²
4. **Policy + approvals + local UI**
5. **Packaged exe + silent auto-update** (prototyped in the POC)

## How the download works

CI builds `ufo-agent.exe` (PyInstaller) and uploads it as the build **artifact**;
a Pages job pulls *that exact artifact* and publishes it onto the GitHub Pages
site, so https://posix4e.github.io/ufo-agent serves the freshly-built exe. It's
also mirrored to GitHub Releases for `releases/latest/download/ufo-agent.exe`.

License: MIT
