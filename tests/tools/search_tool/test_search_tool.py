import os

from yaca.tools.search import search_raw, search_tool
from yaca.llm import FailedToolResult, SuccessToolResult


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None, llm=None):
        self.open_files = open_files
        self.CWD = CWD or os.getcwd()
        self.logger = logger
        self.llm = llm


SAMPLE_FILES_DIR = os.path.join(os.path.dirname(__file__), "sample_files")
assert os.path.exists(SAMPLE_FILES_DIR)

REL_SAMPLE_FILES_DIR = os.path.relpath(SAMPLE_FILES_DIR, os.getcwd())
REL_SAMPLE_FILES_DIR = "./" + REL_SAMPLE_FILES_DIR.lstrip("./")


class _StubLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)

    def warning(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)

    def debug(self, message):
        self.messages.append(message)


class _StubLLM:
    def __init__(self, relevant_files):
        self._relevant_files = relevant_files

    def __call__(self, prompt):
        return (
            "{"
            + '"relevant_files": '
            + str(self._relevant_files).replace("'", '"')
            + "}"
        )


def test_successful_search_raw():
    glob_pattern = os.fspath(os.path.join(REL_SAMPLE_FILES_DIR, "*.txt"))
    result = search_raw(glob_pattern, "alpha|beta")
    assert isinstance(result, SuccessToolResult), result
    message = result.txt
    assert message.startswith("<search_results>")
    assert "<result file=" in message
    assert "alpha" in message or "beta" in message


def test_empty_keywords_raw():
    glob_pattern = os.fspath(os.path.join(REL_SAMPLE_FILES_DIR, "*.txt"))
    result = search_raw(glob_pattern, "")
    assert isinstance(result, FailedToolResult)
    assert "non-empty" in result.txt or "non empty" in result.txt


def test_max_results_truncation_raw(yaca_test_cfg):
    many_file = os.path.join(REL_SAMPLE_FILES_DIR, "many_matches.txt")
    result = search_raw(many_file, "alpha", context_lines=0)
    assert isinstance(result, SuccessToolResult), result
    message = result.txt

    assert "truncat" in message.lower()

    max_results = yaca_test_cfg["tools"]["search"]["max_results"]
    assert message.count("<result") == max_results


def test_search_tool_integration():
    glob_pattern = os.fspath(os.path.join(REL_SAMPLE_FILES_DIR, "*.txt"))

    agent = FakeAgent(open_files=[], CWD=os.getcwd())
    agent.logger = _StubLogger()
    agent.llm = _StubLLM(
        [
            os.path.join(REL_SAMPLE_FILES_DIR, "sample1.txt"),
            os.path.join(REL_SAMPLE_FILES_DIR, "sample2.txt"),
        ]
    )

    result = search_tool(
        agent, glob_pattern=glob_pattern, pattern="alpha|beta", reason="find both"
    )
    assert isinstance(result, SuccessToolResult), result
    assert result["success"] is True

    assert "opened" in result.txt.lower()
    assert "sample1.txt" in result.txt
    assert "sample2.txt" in result.txt

    assert agent.open_files == sorted(
        [
            os.path.relpath(os.path.join(SAMPLE_FILES_DIR, "sample1.txt"), agent.CWD),
            os.path.relpath(os.path.join(SAMPLE_FILES_DIR, "sample2.txt"), agent.CWD),
        ]
    )
