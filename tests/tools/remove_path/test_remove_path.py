import os
import tempfile

import pytest

from yaca.llm import SuccessToolResult
from yaca.tools.remove_path import remove_path_tool


class FakeAgent:
    def __init__(self, recycle_bin_path: str, open_files: list[str]):
        self.RECYCLE_BIN = recycle_bin_path
        self.open_files = open_files


@pytest.mark.fast
def test_remove_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            os.makedirs("src", exist_ok=True)
            file_path = os.path.join("src", "hello.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("hello")

            recycle_bin = os.path.join(tmpdir, ".recycle_bin")
            agent = FakeAgent(recycle_bin_path=recycle_bin, open_files=[file_path])

            result = remove_path_tool(agent, "src/hello.txt")

            assert isinstance(result, SuccessToolResult) is True
            assert agent.open_files == []
        finally:
            os.chdir(old_cwd)
