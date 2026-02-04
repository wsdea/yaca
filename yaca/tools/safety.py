import fnmatch
import os
import re

DOTSEP = f".{os.sep}"


def default_ignores():
    return [
        ".git",
        "*.pyc",
        ".*cache",
        "__pycache__",
        "*.egg*",
        ".coverage",
        ".venv*",
        os.path.join(os.getcwd(), ".yaca", ".state"),
        # "tests",  # TO BE REMOVED
    ]


def _load_gitignore():
    gitignore = []
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as f:
            for line in f:
                rule = line.strip()
                if rule and not rule.startswith("#"):
                    gitignore.append(rule)

    return gitignore


def _compile_ignore_rules(user_rules, default_rules, git_rules):
    out = default_rules + git_rules + user_rules
    out = list(set(out))
    # removing negative ignores
    out = [x.rstrip(os.sep) for x in out if not x.startswith("!")]
    return out


def _is_ignored(path: str, rules: list[str]):
    path = path.removeprefix(DOTSEP)

    for pattern in rules:
        # if sep is inside the pattern, we just check the match
        if os.sep in pattern:
            if fnmatch.fnmatch(path, os.path.join(pattern, "*")):
                return True
        else:
            # otherwise, we split and check match on all parts of the split
            split = path.split(os.sep)
            for x in split:
                if fnmatch.fnmatch(x, pattern):
                    return True

    return False


def is_path_allowed(path: str) -> bool:
    """
    Returns True if the given path is within the current working directory
    and is not ignored by .gitignore. Otherwise returns False.
    """
    cwd = os.getcwd()
    abs_path = os.path.abspath(path)

    # Must be inside the current working directory
    if not abs_path.startswith(cwd + os.sep):
        return False

    gitignore_path = os.path.join(cwd, ".gitignore")
    if not os.path.isfile(gitignore_path):
        return True

    gitignore_patterns = _load_gitignore()
    all_rules = _compile_ignore_rules([], default_ignores(), gitignore_patterns)

    # Determine if the path matches any ignore rule
    rel_path = os.path.relpath(abs_path, cwd)
    if _is_ignored(rel_path, all_rules):
        return False

    return True


UNSAFE_KEYWORDS = {
    "eval",
    "exec",
    "compile",
    "input",
    "__import__",
    "globals",
    "locals",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "ctypes",
    "pickle",
    "marshal",
    "multiprocessing",
}
UNSAFE_ATTR_CALLS = {
    ("os", "system"),
    ("os", "remove"),
    ("os", "popen"),
    ("subprocess", "Popen"),
    ("subprocess", "call"),
    ("subprocess", "check_output"),
    ("subprocess", "run"),
}


def code_is_not_safe(code_snippet: str) -> bool:
    """
    Analyze the code snippet for unsafe patterns using AST.
    Returns True if unsafe constructs are detected or on parse errors.
    """
    words = re.split(r"\W+", code_snippet)
    if any(x in UNSAFE_KEYWORDS for x in words):
        return True

    for x, y in UNSAFE_ATTR_CALLS:
        if x in words and y in words:
            return True

    return False
