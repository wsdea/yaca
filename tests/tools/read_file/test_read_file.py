import os
import glob

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
        assert substring in result.txt


def test_read_files_tool_missing_file(tmp_path):
    os.chdir(str(tmp_path))
    missing_path = "missing.txt"
    agent = FakeAgent(open_files=[missing_path], CWD=str(tmp_path))
    result = read_files_tool(agent, [missing_path])
    assert isinstance(result, FailedToolResult)
    assert "missing.txt" in result.txt


def test_read_files_tool_disallowed_path(tmp_path):
    os.chdir(str(tmp_path))
    allowed_path = "allowed.txt"
    disallowed_path = "../nope.txt"
    agent = FakeAgent(open_files=[allowed_path, disallowed_path], CWD=str(tmp_path))
    result = read_files_tool(agent, [disallowed_path])
    assert isinstance(result, SuccessToolResult)
    assert "error reading" in result.txt.lower()
    assert "path not allowed" in result.txt.lower()


def test_read_files_tool_warns_when_too_many_files(tmp_path, yaca_test_cfg):
    os.chdir(str(tmp_path))

    max_files = yaca_test_cfg["tools"]["read_files"]["max_files"]
    for i in range(max_files + 2):
        p = os.path.join(str(tmp_path), f"f{i}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"file {i}\n")

    glob_pattern = os.path.join(str(tmp_path), "*.txt")
    paths = sorted(glob.glob(glob_pattern))
    agent = FakeAgent(open_files=paths, CWD=str(tmp_path))

    result = read_files_tool(agent, paths)
    assert isinstance(result, SuccessToolResult)

    assert (
        f"Warning, only showing the first {max_files} files of your list" in result.txt
    )
