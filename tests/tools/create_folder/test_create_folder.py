import os

import pytest

from yaca.tools.create_folder import create_folder_tool


@pytest.mark.parametrize("folder_name", ["subdir1", "subdir2"])
def test_create_folder(tmp_path, folder_name):
    target_path = tmp_path / folder_name
    result = create_folder_tool(str(target_path))
    assert result["success"]
    assert os.path.isdir(str(target_path))
