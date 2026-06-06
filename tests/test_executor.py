import asyncio

from agent.executor import run_command


def _collect(lines: list[str]):
    async def on_line(line: str) -> None:
        lines.append(line)

    return on_line


async def _run(cmd: str, lines: list[str]) -> int:
    return await run_command(cmd, _collect(lines))


def test_run_command_streams_output_and_exit_code():
    lines: list[str] = []
    code = asyncio.run(_run("echo hello-exec", lines))
    assert code == 0
    assert any("hello-exec" in ln for ln in lines)


def test_run_command_nonzero_exit():
    lines: list[str] = []
    code = asyncio.run(_run("exit 3", lines))
    assert code == 3
