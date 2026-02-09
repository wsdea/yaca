import os
import tempfile

from yaca.tools.task_completion import validate_python_syntax
from yaca.llm import FailedToolResult, SuccessToolResult


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_validate_python_syntax_all_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "a.py")
        file2 = os.path.join(tmpdir, "b.py")
        write_file(file1, "def foo():\n    return 1\n")
        write_file(file2, "x = 42\n")

        result = validate_python_syntax([file1, file2])
        assert isinstance(result, SuccessToolResult)
        assert "All Python files have valid syntax." in result.txt


def test_validate_python_syntax_ignores_non_py_and_aggregates_errors():
    with tempfile.TemporaryDirectory() as tmpdir:
        valid_file = os.path.join(tmpdir, "valid.py")
        invalid_file1 = os.path.join(tmpdir, "invalid1.py")
        invalid_file2 = os.path.join(tmpdir, "invalid2.py")
        non_py = os.path.join(tmpdir, "other_file.pdf")

        write_file(valid_file, "y = 5\n")
        write_file(invalid_file1, "def broken()\n    pass\n")
        write_file(invalid_file2, "def broken2(:\n    pass\n")
        write_file(non_py, "%PDF-1.4\n")

        result = validate_python_syntax(
            [valid_file, invalid_file1, invalid_file2, non_py]
        )
        assert isinstance(result, FailedToolResult)
        assert "Syntax error" in result.txt
        assert "invalid1.py" in result.txt
        assert "invalid2.py" in result.txt
        assert "other_file.pdf" not in result.txt
