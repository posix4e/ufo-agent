"""PyInstaller entry point for the installed app — launches the tray UI.

The shipped exe is the windowed tray app. The typer CLI (version/status, and
later pair/start) stays available for dev/debug via `python -m agent`.
"""

from agent.tray import main

if __name__ == "__main__":
    main()
