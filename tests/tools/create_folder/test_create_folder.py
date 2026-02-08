import os

import pytest

from yaca.tools.create_folder import create_folder_tool
from yaca.llm import SuccessToolResult


class FakeAgent:
    def __init__(self, open_files, CWD=None, logger=None):
        self.open_files = open_files
        self.CWD = CWD
        self.logger = logger


@pytest.mark.parametrize("folder_name", ["subdir1", "subdir2"])
def test_create_folder(tmp_path, folder_name):
    os.chdir(str(tmp_path))
    target_path = folder_name

    agent = FakeAgent(open_files=[], CWD=str(tmp_path))

    result = create_folder_tool(agent, target_path)
    assert isinstance(result, SuccessToolResult)
    assert os.path.isdir(target_path)
