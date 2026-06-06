"""PyInstaller entry point for ufo-agent.exe.

A stable analysis root for PyInstaller; delegates to the Typer CLI.
"""

from agent.cli import app

if __name__ == "__main__":
    app()
