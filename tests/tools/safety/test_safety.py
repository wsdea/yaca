import pytest

from yaca.tools.safety import code_is_not_safe

test_cases = [
    # Safe
    ("x = 1\nprint(x)", False),
    ("def foo():\n    return 42", False),
    ("import os", False),
    ("os.path.join", False),
    ("def remove(thing):pass", False),
    # UNSAFE
    ("os.remove", True),
    ("os.system", True),
    ("os.system()", True),
    ("from os import remove", True),
    # Unsafe builtins
    ("eval('2 + 2')", True),
    ("exec('print(1)')", True),
    # Unsafe module imports and calls
    ("import os\nos.system('ls')", True),
    ("from subprocess import Popen\nPopen(['ls'])", True),
    ("import pickle\npickle.loads(data)", True),
    ("import socket\ns = socket.socket()", True),
]


@pytest.mark.fast
@pytest.mark.parametrize("code_snippet,expected", test_cases)
def test_code_is_not_safe_detection(code_snippet, expected):
    assert code_is_not_safe(code_snippet) is expected
