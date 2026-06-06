from typer.testing import CliRunner

from agent import __version__
from agent.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__.split("-")[0] in result.stdout


def test_status():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "device_name" in result.stdout
