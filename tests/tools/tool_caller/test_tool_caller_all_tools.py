import os

from yaca.tools.tool_caller import ToolCaller


def test_tool_caller_basic_tools():
    """Test basic tools via ToolCaller."""
    caller = ToolCaller()

    # list_files
    result = caller(
        "list_files",
        glob_pattern="./tests/tools/search_tool/sample_files/*.txt",
        max_depth="2",
    )
    assert result.get("success"), f"list_files failed: {result}"

    # read_file
    result = caller(
        "read_file",
        path="yaca/tools/read_file.py",
    )
    assert result.get("success"), f"read_file failed: {result}"

    # reply_to_user
    result = caller(
        "reply_to_user",
        message="Hello from test",
    )
    assert result.get("success"), f"reply_to_user failed: {result}"

    # search
    result = caller(
        "search",
        glob_pattern="./tests/tools/search_tool/sample_files/*.txt",
        keywords='["alpha"]',
    )
    assert result.get("success"), f"search failed: {result}"


def test_tool_caller_create_and_apply(tmp_path):
    """Test create_file and apply_diff tools."""
    caller = ToolCaller()

    file_path = tmp_path / "test.txt"

    # create_file
    result = caller(
        "create_file",
        path=str(file_path),
        content="Hello world",
    )
    assert result.get("success"), f"create_file failed: {result}"
    assert os.path.isfile(file_path), "File was not created"

    # apply_diff
    result = caller(
        "apply_diff",
        file_path=str(file_path),
        search_text="Hello",
        replace_text="Hi",
        allow_multiple_matches="false",
    )
    assert result.get("success"), f"apply_diff failed: {result}"

    # verify content changed
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Hi world" in content, "apply_diff did not modify the file as expected"


def test_tool_caller_attempt_completion():
    """Test attempt_completion tool (does not assert success to avoid external dependencies)."""
    caller = ToolCaller()
    result = caller("attempt_completion")
    # Ensure the tool returns a dict with a 'success' key
    assert isinstance(result, dict), "attempt_completion did not return a dict"
    assert "success" in result, "attempt_completion result missing 'success' key"
