import pytest

from yaca.tools.tool_caller import ToolCaller


@pytest.mark.parametrize(
    "tool_name, kwargs",
    [
        (
            "list_files",
            {
                "glob_pattern": "./tests/tools/search_tool/sample_files/*.txt",
                "max_depth": "2",
            },
        ),
        (
            "read_file",
            {
                "path": "yaca/tools/read_file.py",
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
                "keywords": '["alpha"]',
            },
        ),
        (
            "attempt_completion",
            {},
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
    caller = ToolCaller()
    result = caller(tool_name, **kwargs)

    # All tools should return a dict
    assert isinstance(result, dict), f"{tool_name} did not return a dict"

    if tool_name == "attempt_completion":
        # Only verify that the key exists; the value may be False if external checks fail
        assert "success" in result, "attempt_completion result missing 'success' key"
    else:
        # For the other tools we expect a successful execution
        assert result.get("success") is True, f"{tool_name} failed: {result}"
