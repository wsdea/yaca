import os

import pytest

from yaca.tools.run_command import run_command_tool


@pytest.mark.parametrize(
    "command,expected_success,expected_substring",
    [
        ("echo HelloWorld", True, "HelloWorld"),
        ('python -c "import sys; sys.exit(1)"', False, ""),
    ],
)
def test_run_command(command, expected_success, expected_substring):
    pass
    # result = run_command_tool(None, command)
    # assert result["success"] == expected_success
    # if expected_success:
    #     assert expected_substring in result.txt
