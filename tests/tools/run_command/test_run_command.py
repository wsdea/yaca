import os
import subprocess

import pytest

from yaca.llm import FailedToolResult, SuccessToolResult
from yaca.tools.run_command import run_command_tool


class FakeAgent:
    def __init__(self, disable_run_command: bool = False):
        self.disable_run_command = disable_run_command


class FakeTimeoutExpired(subprocess.TimeoutExpired):
    def __init__(self, cmd, timeout, stdout=None, stderr=None):
        super().__init__(cmd=cmd, timeout=timeout, output=stdout, stderr=stderr)


@pytest.mark.parametrize(
    "command,expected_success",
    [
        ("echo HelloWorld", True),
        ('python -c "import sys; sys.exit(1)"', False),
    ],
)
def test_run_command(command, expected_success):
    agent = FakeAgent(disable_run_command=False)
    result = run_command_tool(agent, command)

    if expected_success:
        assert isinstance(result, SuccessToolResult)
        assert "<stdout>" in result.txt
        assert "</stdout>" in result.txt
        assert "HelloWorld" in result.txt
    else:
        assert isinstance(result, FailedToolResult)
        assert "<stdout>" in result.txt
        assert "</stdout>" in result.txt
        assert "<stderr>" in result.txt
        assert "</stderr>" in result.txt
        assert "exit code" in result.txt.lower()


def test_run_command_timeout(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FakeTimeoutExpired(
            cmd=kwargs["args"] if "args" in kwargs else args[0],
            timeout=0.01,
            stdout=b"partial out\n",
            stderr=b"partial err\n",
        )

    monkeypatch.setattr("yaca.tools.run_command.subprocess.run", fake_run)

    agent = FakeAgent(disable_run_command=False)
    result = run_command_tool(agent, "echo Hello", timeout=1)

    assert isinstance(result, FailedToolResult)
    assert "timed out" in result.txt.lower()
    assert "<stdout>" in result.txt
    assert "partial out" in result.txt
    assert "<stderr>" in result.txt
    assert "partial err" in result.txt


def test_run_command_disabled(tmp_path):
    sentinel = os.path.join(str(tmp_path), "sentinel.txt")
    command = f'python -c "open(r"{sentinel}", "w").write("x")"'

    agent = FakeAgent(disable_run_command=True)
    result = run_command_tool(agent, command)

    assert isinstance(result, SuccessToolResult)
    assert ("disabled" in result.txt.lower()) or ("unsafe" in result.txt.lower())
    assert not os.path.exists(sentinel)
