"""ufo-agent CLI.

The installed app launches the tray UI; these commands are for dev/debug and
headless use:
    python -m agent version
    python -m agent status
    python -m agent pair --code ABCD-1234 --relay http://host:8000
    python -m agent connect        # run the relay client (auto-enrolls on the tailnet)
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from .config import VERSION, Settings
from .identity import OnboardError, claim
from .relay_client import RelayClient
from .runtime import AgentRuntime
from .storage import Storage

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
    """Show local identity / pairing status."""
    state = Storage().load()
    data = state.model_dump()
    if data.get("device_token"):
        data["device_token"] = data["device_token"][:6] + "...(masked)"
    console.print_json(data=data)
    console.print(f"paired: {state.paired}")


@app.command()
def pair(
    code: str = typer.Option(..., help="Pairing code from the control plane"),
    relay: str = typer.Option(None, help="Control plane URL (default: the hosted one)"),
) -> None:
    """Claim a pairing code. Defaults to the hosted control plane; --relay overrides."""
    settings = Settings()
    storage = Storage()
    state = storage.load()
    relay = relay or settings.control_plane_url
    try:
        state = claim(storage, state, code=code, relay_url=relay, device_name=settings.device_name)
    except OnboardError as exc:
        console.print(f"[red]Pairing failed:[/red] {exc}")
        raise typer.Exit(code=1)
    console.print(f"[green]Paired![/green] device_id={state.device_id}")


@app.command()
def connect() -> None:
    """Run the relay client headless (auto-enrolls on the tailnet if unpaired)."""
    settings = Settings()
    storage = Storage()
    runtime = AgentRuntime()
    client = RelayClient(settings, storage, runtime)
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app()
