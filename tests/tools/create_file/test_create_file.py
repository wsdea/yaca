import os

import pytest

from yaca.tools.create_file import create_file_tool
from yaca.tools.read_files import read_file
from yaca.llm import SuccessToolResult


class FakeLogger:
    def debug(self, *args, **kwargs):
        pass


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None, disable_run_command=False):
        self.open_files = open_files
        self.CWD = CWD
        self.logger = logger if logger is not None else FakeLogger()
        self.disable_run_command = disable_run_command


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("test1.txt", "content1"),
    ],
)
def test_create_file(tmp_path, filename, expected):
    os.chdir(str(tmp_path))
    target_path = filename

    agent = FakeAgent(open_files=[target_path], CWD=str(tmp_path))

    result = create_file_tool(agent, target_path, expected)
    assert isinstance(result, SuccessToolResult)
    assert target_path in result.message

    read_result = read_file(target_path)
    assert read_result == expected
