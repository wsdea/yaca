import pytest

from yaca.tools.read_files import read_file


@pytest.mark.parametrize(
    "path,expected",
    [
        ("tests/tools/read_file/sample.txt", "Hello Read"),
    ],
)
def test_read_file(path, expected):
    result = read_file(path)
    assert result == expected
