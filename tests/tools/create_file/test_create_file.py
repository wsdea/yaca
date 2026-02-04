import os

import pytest

from yaca.tools.create_file import create_file_tool
from yaca.tools.read_files import read_file


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("test1.txt", "content1"),
    ],
)
def test_create_file(tmp_path, filename, expected):
    # Load expected content from a file in this directory
    target_path = os.path.join(tmp_path, filename)

    result = create_file_tool(None, target_path, expected)
    assert result["success"]

    read_result = read_file(target_path)
    assert read_result == expected
