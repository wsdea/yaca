import os

from yaca.tools.list_files import list_files_tool


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None):
        self.open_files = open_files
        self.CWD = CWD
        self.logger = logger


def test_list_files():
    agent = FakeAgent(open_files=[])

    result = list_files_tool(agent, "tests/tools/list_files/**", return_message=True)
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert output.startswith("<list_files_result>\n")
    assert output.endswith("\n</list_files_result>")
    assert "sample.txt" in output
    assert "bar.txt" in output
    assert "yes.py" in output
    assert "bar2.txt" in output
    assert "../" not in output

    result = list_files_tool(
        agent,
        "tests/tools/list_files/**",
        ignore_patterns=["bar*"],
        return_message=True,
    )
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "sample.txt" in output
    assert "bar.txt" in output
    assert "yes.py" in output
    assert "bar2.txt" in output

    result = list_files_tool(
        agent, "tests/tools/list_files/**/*.py", return_message=True
    )
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "sample.txt" not in output
    assert "bar.txt" not in output
    assert "yes.py" in output
    assert "bar2.txt" not in output

    result = list_files_tool(agent, "tests/tools/list_files/**", return_message=True)
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "- foo/" in output or "foo/" in output
    assert "- foo2/" in output or "foo2/" in output
    assert "foo2\n" not in output
    assert "<" in output and "hidden items" in output

    result = list_files_tool(
        agent,
        "tests/tools/list_files/foo/**",
        ignore_patterns=["bar*"],
        return_message=True,
    )
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "sample.txt" not in output
    assert "bar.txt" in output
    assert "yes.py" in output
    assert "bar2.txt" in output

    assert os.sep not in "\n"
