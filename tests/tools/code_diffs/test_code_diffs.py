import pytest

from yaca.tools.code_diffs import apply_diff_tool, search_replace_diff_tool
from yaca.tools.read_files import read_file


@pytest.fixture
def sample_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "sample.txt"
    content = "line1\\nreplace_me\\nline3\\nreplace_me\\nline5\\n"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def test_search_replace_success(tmp_path):
    file_path = tmp_path / "single.txt"
    file_path.write_text("foo replace_me bar", encoding="utf-8")
    result = search_replace_diff_tool(str(file_path), "replace_me", "REPLACED")
    assert result["success"]
    assert "Replaced 1 occurrence" in result["message"]
    assert read_file(str(file_path)) == "foo REPLACED bar"


def test_search_replace_no_match(tmp_path):
    file_path = tmp_path / "nomatch.txt"
    original = "nothing to change here"
    file_path.write_text(original, encoding="utf-8")
    result = search_replace_diff_tool(str(file_path), "absent", "new")
    assert not result["success"]
    assert "No matches found" in result["message"]
    assert read_file(str(file_path)) == original


def test_search_replace_multiple_without_allow(tmp_path):
    file_path = tmp_path / "multiple.txt"
    file_path.write_text("a replace_me b replace_me c", encoding="utf-8")
    result = search_replace_diff_tool(str(file_path), "replace_me", "X")
    assert not result["success"]
    assert "Multiple (2) matches" in result["message"]
    # file should stay unchanged
    assert read_file(str(file_path)) == "a replace_me b replace_me c"


def test_search_replace_multiple_with_allow(tmp_path):
    file_path = tmp_path / "multiple_allow.txt"
    file_path.write_text("x replace_me y replace_me z", encoding="utf-8")
    result = search_replace_diff_tool(
        str(file_path), "replace_me", "Y", allow_multiple_matches=True
    )
    assert result["success"]
    assert "Replaced 2 occurrence" in result["message"]
    assert read_file(str(file_path)) == "x Y y Y z"


def test_apply_diff_success(tmp_path):
    file_path = tmp_path / "diff.txt"
    file_path.write_text("first line\\nsecond line\\nthird line", encoding="utf-8")
    diff = (
        "<diff_search_1>second line</diff_search_1>"
        "<diff_replace_1>SECOND</diff_replace_1>"
    )
    result = apply_diff_tool(str(file_path), diff)
    assert result["success"]
    assert "Applied 1 diff block" in result["message"]
    assert read_file(str(file_path)) == "first line\\nSECOND\\nthird line"


def test_apply_diff_mismatched_blocks(tmp_path):
    file_path = tmp_path / "mismatch.txt"
    file_path.write_text("a b c", encoding="utf-8")
    diff = "<diff_search_1>a b c</diff_search_1><diff_replace_2>XYZ</diff_replace_2>"
    result = apply_diff_tool(str(file_path), diff)
    assert not result["success"]
    assert "Non-matching diff block indices" in result["message"]
    # content unchanged
    assert read_file(str(file_path)) == "a b c"


def test_apply_diff_empty_diff(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("content", encoding="utf-8")
    result = apply_diff_tool(str(file_path), "")
    assert not result["success"]
    assert "diff text is empty" in result["message"]
    assert read_file(str(file_path)) == "content"
