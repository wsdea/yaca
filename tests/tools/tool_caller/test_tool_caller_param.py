import pytest

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


@pytest.mark.parametrize(
    "tool_name, kwargs",
    [
        (
            "list_files",
            {
                "glob_pattern": "./tests/tools/search_tool/sample_files/*.txt",
            },
        ),
        (
            "read_files",
            {
                "files": '["yaca/tools/read_files.py"]',
            },
        ),
        (
            "reply_to_user",
            {
                "message": "test message from param test",
            },
        ),
        (
            "search",
            {
                "glob_pattern": "./tests/tools/search_tool/sample_files/*.txt",
                "pattern": "alpha",
                "reason": "param test search",
            },
        ),
        (
            "attempt_completion",
            {"recap": "test recap"},
        ),
    ],
)
def test_tool_caller_parametrized(tool_name, kwargs):
    """
    Quick parametrized test that exercises each exposed tool in ToolCaller.
    It checks that the tool returns a dict and, for most tools, that the
    ``success`` key is True.  ``attempt_completion`` is only verified to
    return a dict containing a ``success`` key because it may depend on
    external commands.
    """
    all_tools = {
        "list_files": list_files_tool,
        "read_files": read_files_tool,
        "reply_to_user": reply_to_user_tool,
        "search": search_tool,
        "attempt_completion": attempt_completion_tool,
    }
    caller = ToolCaller(all_tools=all_tools, hook_caller=None)
    caller.set_tools(list(all_tools.keys()))
    agent = FakeAgent()
    kwargs = dict(kwargs)
    kwargs["agent"] = agent
    result = caller(tool_name, **kwargs)

    if tool_name == "attempt_completion":
        assert isinstance(
            result, AssistantResponse
        ), f"{tool_name} did not return an AssistantResponse"
    else:
        assert isinstance(result, SuccessToolResult), f"{tool_name} failed: {result}"
