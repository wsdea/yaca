import os

from yaca.tools.search import search_raw, search_tool
from yaca.llm import FailedToolResult


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None, llm=None):
        self.open_files = open_files
        self.CWD = CWD
        self.logger = logger
        self.llm = llm


SAMPLE_FILES_DIR = os.path.join("tests", "tools", "search_tool", "sample_files")
assert os.path.exists(SAMPLE_FILES_DIR)


class _StubLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)

    def warning(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)


class _StubLLM:
    def __init__(self, text):
        self._text = text

    def complete(self, prompt):
        return self._text


def test_successful_search_raw():
    pattern = os.path.join(SAMPLE_FILES_DIR, "*.txt")
    result = search_raw(pattern, "alpha|beta")
    assert result["success"] is True, result["message"]
    message = result["message"]
    assert "<search_results>" in message
    assert "<result file=" in message
    assert "alpha" in message
    assert "beta" in message


def test_empty_keywords_raw():
    pattern = os.path.join(SAMPLE_FILES_DIR, "*.txt")
    result = search_raw(pattern, "")
    assert isinstance(result, FailedToolResult)
    assert "pattern needs to be a non empty string" in result.txt


def test_max_results_truncation_raw():
    many_file = os.path.join(SAMPLE_FILES_DIR, "many_matches.txt")
    result = search_raw(many_file, "alpha", context_lines=0)
    assert result["success"] is True, result["message"]
    message = result["message"]
    assert "truncated" in message
    assert message.count("<result") == 30


def test_search_tool_integration():
    pattern = os.path.join(SAMPLE_FILES_DIR, "*.txt")

    agent = FakeAgent(open_files=[])
    agent.logger = _StubLogger()
    agent.llm = _StubLLM("Reason: looking for alpha and beta")

    result = search_tool(
        agent, glob_pattern=pattern, pattern="alpha|beta", reason="find both"
    )
    assert result["success"] is True, result["message"]
    message = result["message"]
    assert "<search_results>" in message
    assert "alpha" in message
    assert "beta" in message
