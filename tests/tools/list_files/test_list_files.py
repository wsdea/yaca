import os

from yaca.llm import SuccessToolResult
from yaca.tools.list_files import list_files, list_files_tool


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None):
        self.open_files = open_files
        self.CWD = CWD
        self.logger = logger


def test_list_files():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    os.chdir(repo_root)

    agent = FakeAgent(open_files=[])

    result = list_files_tool(agent, "./tests/tools/list_files/**", return_message=True)
    assert isinstance(result, SuccessToolResult)
    output = result.txt
    assert output.startswith("<list_files_result>\n")
    assert output.endswith("\n</list_files_result>")
    assert "sample.txt" in output
    assert "bar.txt" in output
    assert "yes.py" in output
    assert "bar2.txt" in output
    assert ".." not in output

    matched_files = list_files("./tests/tools/list_files/**", ignore_patterns=["bar*"])
    assert "tests/tools/list_files/sample.txt" in matched_files
    assert "tests/tools/list_files/bar.txt" not in matched_files
    assert "tests/tools/list_files/foo/yes.py" in matched_files
    assert "tests/tools/list_files/foo2/bar2.txt" not in matched_files

    result = list_files_tool(
        agent, "./tests/tools/list_files/**/*.py", return_message=True
    )
    assert isinstance(result, SuccessToolResult)
    output = result.txt
    assert "sample.txt" not in output
    assert "bar.txt" not in output
    assert "yes.py" in output
    assert "bar2.txt" not in output

    result = list_files_tool(agent, "./tests/tools/list_files/**", return_message=True)
    assert isinstance(result, SuccessToolResult)
    output = result.txt
    assert "foo" in output
    assert "foo2" in output
    assert "<" in output

    matched_files = list_files(
        "./tests/tools/list_files/foo/**", ignore_patterns=["bar*"]
    )
    assert "tests/tools/list_files/foo/bar.txt" not in matched_files
    assert "tests/tools/list_files/foo/yes.py" in matched_files
    assert "tests/tools/list_files/foo/bar2.txt" not in matched_files

    assert os.sep not in "\n"
