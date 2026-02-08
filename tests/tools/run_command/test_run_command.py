import os

import pytest

from yaca.tools.run_command import run_command_tool


class FakeAgent:
    def __init__(self, disable_run_command: bool = False):
        self.disable_run_command = disable_run_command


@pytest.mark.parametrize(
    "command,expected_success,expected_substring",
    [
        ("echo HelloWorld", True, "HelloWorld"),
        ('python -c "import sys; sys.exit(1)"', False, ""),
    ],
)
def test_run_command(command, expected_success, expected_substring):
    agent = FakeAgent(disable_run_command=False)
    result = run_command_tool(agent, command)

    assert result.success is expected_success
    if expected_success:
        assert expected_substring in result.message
    else:
        assert result.message != ""


def test_run_command_disabled(tmp_path):
    sentinel = tmp_path / "sentinel.txt"
    command = f'python -c "open(r"{str(sentinel)}", "w").write("x")"'

    agent = FakeAgent(disable_run_command=True)
    result = run_command_tool(agent, command)

    assert result.success is True
    assert result.message != ""
    assert not os.path.exists(str(sentinel))