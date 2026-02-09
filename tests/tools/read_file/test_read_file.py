import os

import pytest

from yaca.tools.read_files import read_files_tool
from yaca.llm import FailedToolResult, SuccessToolResult


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None):
        self.open_files = open_files
        self.CWD = CWD
        self.logger = logger


@pytest.mark.parametrize(
    "path,expected_substrings",
    [
        (
            os.fspath(os.path.join(os.path.dirname(__file__), "sample.txt")),
            [
                "<read_files_answer>",
                "<content file=",
                "Hello Read",
                "</read_files_answer>",
            ],
        ),
    ],
)
def test_read_files_tool(path, expected_substrings):
    agent = FakeAgent(open_files=[path], CWD=os.path.dirname(path))
    result = read_files_tool(agent, [path])
    assert isinstance(result, SuccessToolResult)
    for substring in expected_substrings:
        assert substring in result.message


def test_read_files_tool_missing_file(tmp_path):
    os.chdir(str(tmp_path))
    missing_path = "missing.txt"
    agent = FakeAgent(open_files=[missing_path], CWD=str(tmp_path))
    result = read_files_tool(agent, [missing_path])
    assert isinstance(result, FailedToolResult)
    assert "missing.txt" in result.message


def test_read_files_tool_disallowed_path(tmp_path):
    os.chdir(str(tmp_path))
    allowed_path = "allowed.txt"
    disallowed_path = "../nope.txt"
    agent = FakeAgent(open_files=[allowed_path, disallowed_path], CWD=str(tmp_path))
    result = read_files_tool(agent, [disallowed_path])
    assert isinstance(result, FailedToolResult)
    assert "not allowed" in result.message.lower()