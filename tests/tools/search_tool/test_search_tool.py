import os

from yaca.tools.search import search_tool

SAMPLE_FILES_DIR = os.path.join("tests", "tools", "search_tool", "sample_files")
assert os.path.exists(SAMPLE_FILES_DIR)


def test_successful_search():
    pattern = os.path.join(SAMPLE_FILES_DIR, "*.txt")
    result = search_tool([pattern], "alpha|beta")
    assert result["success"] is True, result["message"]
    message = result["message"]
    assert "<search_results>" in message
    assert "<result file=" in message
    # Ensure both keywords appear in the output
    assert "alpha" in message
    assert "beta" in message


def test_empty_keywords():
    pattern = os.path.join(SAMPLE_FILES_DIR, "*.txt")
    result = search_tool([pattern], "")
    assert result["success"] is False, result["message"]
    assert "pattern needs to be a non empty string" in result["message"]


def test_max_results_truncation():
    many_file = os.path.join(SAMPLE_FILES_DIR, "many_matches.txt")
    result = search_tool([many_file], "alpha", context_lines=0)
    assert result["success"] is True, result["message"]
    message = result["message"]
    # Warning about truncation should be present
    assert "truncated" in message
    # Exactly 30 result blocks should be present
    assert message.count("<result") == 30
