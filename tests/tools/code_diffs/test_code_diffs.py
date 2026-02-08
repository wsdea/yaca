import os

from yaca.tools.code_diffs import apply_diff_tool, search_replace_diff_tool
from yaca.tools.read_files import read_file
from yaca.llm import FailedToolResult, SuccessToolResult


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None, disable_run_command=False):
        self.open_files = open_files
        self.CWD = CWD
        self.logger = logger
        self.disable_run_command = disable_run_command


def _make_agent(file_path, tmp_path):
    return FakeAgent(open_files=[file_path], CWD=str(tmp_path))


def test_search_replace_success(tmp_path):
    os.chdir(str(tmp_path))
    file_path = "single.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("foo replace_me bar")

    agent = _make_agent(file_path, tmp_path)

    result = search_replace_diff_tool(agent, file_path, "replace_me", "REPLACED")
    assert isinstance(result, SuccessToolResult)
    assert "Replaced 1 occurrence" in result.txt
    assert read_file(file_path) == "foo REPLACED bar"


def test_search_replace_no_match(tmp_path):
    os.chdir(str(tmp_path))
    file_path = "nomatch.txt"
    original = "nothing to change here"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(original)

    agent = _make_agent(file_path, tmp_path)

    result = search_replace_diff_tool(agent, file_path, "absent", "new")
    assert isinstance(result, FailedToolResult)
    assert "No matches found" in result.txt
    assert read_file(file_path) == original


def test_search_replace_multiple_without_allow(tmp_path):
    os.chdir(str(tmp_path))
    file_path = "multiple.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("a replace_me b replace_me c")

    agent = _make_agent(file_path, tmp_path)

    result = search_replace_diff_tool(agent, file_path, "replace_me", "X")
    assert isinstance(result, FailedToolResult)
    assert "Multiple (2) matches" in result.txt
    assert read_file(file_path) == "a replace_me b replace_me c"


def test_search_replace_multiple_with_allow(tmp_path):
    os.chdir(str(tmp_path))
    file_path = "multiple_allow.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("x replace_me y replace_me z")

    agent = _make_agent(file_path, tmp_path)

    result = search_replace_diff_tool(
        agent, file_path, "replace_me", "Y", allow_multiple_matches=True
    )
    assert isinstance(result, SuccessToolResult)
    assert "Replaced 2 occurrence" in result.txt
    assert read_file(file_path) == "x Y y Y z"


def test_apply_diff_success(tmp_path):
    os.chdir(str(tmp_path))
    file_path = "diff.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("first line\nsecond line\nthird line")

    agent = _make_agent(file_path, tmp_path)

    diff = (
        "<diff_search_1>second line</diff_search_1>"
        "<diff_replace_1>SECOND</diff_replace_1>"
    )
    result = apply_diff_tool(agent, file_path, diff)
    assert isinstance(result, SuccessToolResult)
    assert "Applied 1 diff block" in result.txt
    assert read_file(file_path) == "first line\nSECOND\nthird line"


def test_apply_diff_mismatched_blocks(tmp_path):
    os.chdir(str(tmp_path))
    file_path = "mismatch.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("a b c")

    agent = _make_agent(file_path, tmp_path)

    diff = "<diff_search_1>a b c</diff_search_1><diff_replace_2>XYZ</diff_replace_2>"
    result = apply_diff_tool(agent, file_path, diff)
    assert isinstance(result, FailedToolResult)
    assert "Non-matching diff block indices" in result.txt
    assert read_file(file_path) == "a b c"


def test_apply_diff_empty_diff(tmp_path):
    os.chdir(str(tmp_path))
    file_path = "empty.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("content")

    agent = _make_agent(file_path, tmp_path)

    result = apply_diff_tool(agent, file_path, "")
    assert isinstance(result, FailedToolResult)
    assert "diff text is empty" in result.txt
    assert read_file(file_path) == "content"
