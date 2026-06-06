"""ufo-agent CLI (skeleton).

Today: version / status. The substance — pairing, the outbound WebSocket client
to the control plane, the GUI automation backend (eventually Microsoft UFO²),
policy, approvals, and the local UI — grows here deliberately. Reference POC:
https://github.com/posix4e/ufo-device-agent

Run:
    python -m agent version
    python -m agent status
"""

from __future__ import annotations

import typer
from rich.console import Console

from .config import VERSION, Settings

app = typer.Typer(
    help="UFO agent — pair this Windows PC to a control plane and let a remote AI use it.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Print the agent version."""
    console.print(f"ufo-agent {VERSION}")


@app.command()
def status() -> None:
    """Show local identity / pairing status (skeleton)."""
    settings = Settings()
    console.print_json(
        data={
            "version": VERSION,
            "device_name": settings.device_name,
            "relay_url": settings.relay_url,
            "paired": False,  # TODO: read persisted pairing state
        }
    )


# TODO(grow deliberately):
#   pair  --code XXXX-XXXX --relay https://...   (claim a code → store device token)
#   start                                        (outbound relay client + local UI)
#   unpair


if __name__ == "__main__":
    app()
