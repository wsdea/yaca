import os

from yaca.tools.code_diffs import apply_diff_tool
from yaca.tools.create_file import create_file_tool
from yaca.tools.list_files import list_files_tool
from yaca.tools.read_files import read_files_tool
from yaca.tools.reply_to_user import reply_to_user_tool
from yaca.tools.search import search_tool
from yaca.tools.task_completion import attempt_completion_tool
from yaca.tools.tool_caller import ToolCaller
from yaca.llm import AssistantResponse, SuccessToolResult


class FakeAgent:
    def __init__(self):
        self.messages = []
        self.open_files = []
        self.CWD = os.getcwd()

        class _Logger:
            def debug(self, *args, **kwargs):
                pass

            def info(self, *args, **kwargs):
                pass

            def warning(self, *args, **kwargs):
                pass

            def error(self, *args, **kwargs):
                pass

        self.logger = _Logger()

        def _llm(*args, **kwargs):
            return None

        self.llm = _llm
        self.disable_run_command = True


def test_tool_caller_basic_tools():
    """Test basic tools via ToolCaller."""
    all_tools = {
        "list_files": list_files_tool,
        "read_files": read_files_tool,
        "reply_to_user": reply_to_user_tool,
        "search": search_tool,
    }
    caller = ToolCaller(all_tools=all_tools, hook_caller=None)
    caller.set_tools(["list_files", "read_files", "reply_to_user", "search"])
    agent = FakeAgent()

    result = caller(
        "list_files",
        agent=agent,
        glob_pattern="./tests/tools/search_tool/sample_files/*.txt",
    )
    assert isinstance(result, SuccessToolResult), f"list_files failed: {result}"

    result = caller(
        "read_files",
        agent=agent,
        files='["yaca/tools/read_files.py"]',
    )
    assert isinstance(result, SuccessToolResult), f"read_files failed: {result}"

    result = caller(
        "reply_to_user",
        agent=agent,
        message="Hello from test",
    )
    assert isinstance(result, SuccessToolResult), f"reply_to_user failed: {result}"

    result = caller(
        "search",
        agent=agent,
        glob_pattern="./tests/tools/search_tool/sample_files/*.txt",
        pattern="alpha",
        reason="test search",
    )
    assert isinstance(result, SuccessToolResult), f"search failed: {result}"


def test_tool_caller_create_and_apply():
    """Test create_file and apply_diff tools."""
    all_tools = {
        "create_file": create_file_tool,
        "apply_diff": apply_diff_tool,
    }
    caller = ToolCaller(all_tools=all_tools, hook_caller=None)
    caller.set_tools(["create_file", "apply_diff"])
    agent = FakeAgent()

    file_path = "tests/tools/tool_caller/tmp_test.txt"
    agent.open_files = [file_path]

    try:
        result = caller(
            "create_file",
            agent=agent,
            path=file_path,
            content="Hello world",
        )
        assert isinstance(result, SuccessToolResult), f"create_file failed: {result}"
        assert os.path.isfile(file_path), "File was not created"

        result = caller(
            "apply_diff",
            agent=agent,
            file_path=file_path,
            diffs=(
                """
<apply_diff>
<file_path>{file_path}</file_path>
<diffs>
<diff_search_1>Hello</diff_search_1>
<diff_replace_1>Hi</diff_replace_1>
</diffs>
</apply_diff>
""".format(file_path=file_path).strip()
            ),
        )
        assert isinstance(result, SuccessToolResult), f"apply_diff failed: {result}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Hi world" in content, "apply_diff did not modify the file as expected"
    finally:
        if os.path.isfile(file_path):
            os.remove(file_path)


def test_tool_caller_attempt_completion():
    """Test attempt_completion tool (does not assert success to avoid external dependencies)."""
    all_tools = {"attempt_completion": attempt_completion_tool}
    caller = ToolCaller(all_tools=all_tools, hook_caller=None)
    caller.set_tools(["attempt_completion"])
    agent = FakeAgent()
    result = caller("attempt_completion", agent=agent, recap="test recap")
    assert isinstance(
        result, AssistantResponse
    ), "attempt_completion did not return an AssistantResponse"