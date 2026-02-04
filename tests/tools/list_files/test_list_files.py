from yaca.tools.list_files import list_files_tool


def test_list_files():
    """Test that list_files correctly finds files under 'foo' and excludes 'foo2'."""
    result = list_files_tool(["tests/tools/list_files/**"], max_depth=5)
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "sample.txt" in output
    assert "bar.txt" in output
    assert "yes.py" in output
    assert "bar2.txt" in output
    assert "../" not in output

    result = list_files_tool(
        ["tests/tools/list_files/**"], ignore_patterns=["bar*"], max_depth=5
    )
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "sample.txt" in output
    assert "bar.txt" not in output
    assert "yes.py" in output
    assert "bar2.txt" not in output

    result = list_files_tool(["tests/tools/list_files/**/*.py"], max_depth=5)
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "sample.txt" not in output
    assert "bar.txt" not in output
    assert "yes.py" in output
    assert "bar2.txt" not in output

    result = list_files_tool(["tests/tools/list_files/**"], max_depth=4)
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "foo/" in output
    assert "foo2\n" not in output
    assert "foo2/\n" in output
    assert "yes.py" not in output
    assert "hidden items" in output

    result = list_files_tool(
        ["tests/tools/list_files/**"],
        max_depth=5,
    )
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "foo/" in output
    assert "foo2\n" not in output
    assert "foo2/\n" in output
    assert "yes.py" in output
    assert "hidden items" not in output

    result = list_files_tool(
        ["tests/tools/list_files/foo/**", "tests/tools/list_files/foo2/**"],
        ignore_patterns=["bar*"],
        max_depth=10,
    )
    assert result["success"], f"list_files failed: {result['message']}"
    output = result["message"]
    assert "sample.txt" not in output
    assert "bar.txt" not in output
    assert "yes.py" in output
    assert "bar2.txt" not in output
