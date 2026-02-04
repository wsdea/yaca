import os
import tempfile

from yaca.tools.attempt_completion import validate_python_syntax


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_validate_python_syntax_all_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two valid python files
        file1 = os.path.join(tmpdir, "a.py")
        file2 = os.path.join(tmpdir, "b.py")
        write_file(file1, "def foo():\n    return 1\n")
        write_file(file2, "x = 42\n")

        result = validate_python_syntax([file1, file2])
        assert result["success"] is True
        assert "All Python files have valid syntax." in result["message"]


def test_validate_python_syntax_with_errors():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a valid file and an invalid file
        valid_file = os.path.join(tmpdir, "valid.py")
        invalid_file = os.path.join(tmpdir, "invalid.py")
        write_file(valid_file, "y = 5\n")
        # Syntax error: missing colon
        write_file(invalid_file, "def broken()\n    pass\n")

        result = validate_python_syntax([valid_file, invalid_file, "other_file.pdf"])
        assert result["success"] is False
        # The message should contain the syntax error description
        assert "Syntax error in" in result["message"]
        assert "invalid.py" in result["message"]
        # Ensure only one error message is reported (joined by '; ' if multiple)
        assert result["message"].count("Syntax error in") == 1
