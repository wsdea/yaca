import fnmatch
import os
import re

from ..config import get_cfg_value

DOTSEP = f".{os.sep}"

_UNSAFE_TRIPPED = False


def set_unsafe_tripped() -> None:
    global _UNSAFE_TRIPPED
    _UNSAFE_TRIPPED = True


def is_unsafe_tripped() -> bool:
    return _UNSAFE_TRIPPED


def default_ignores():
    ignore_patterns = get_cfg_value("safety.ignore_patterns", list)
    ignore_patterns = [x.strip() for x in ignore_patterns if isinstance(x, str)]
    ignore_patterns = [x for x in ignore_patterns if x]

    state_rel = os.path.join(".yaca", ".state")
    state_abs = os.path.join(os.getcwd(), ".yaca", ".state")

    if state_rel not in ignore_patterns and state_abs not in ignore_patterns:
        ignore_patterns.append(state_abs)

    return ignore_patterns


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

    git_rules = _load_gitignore()
    all_rules = _compile_ignore_rules([], default_ignores(), git_rules)

    # Determine if the path matches any ignore rule
    rel_path = os.path.relpath(abs_path, cwd)
    if _is_ignored(rel_path, all_rules):
        return False

    return True


def _get_unsafe_keywords() -> set[str]:
    cfg = get_cfg_value("safety.unsafe_keywords", list)

    out = []
    for x in cfg:
        if not isinstance(x, str):
            raise Exception("Unparsable list of unsafe keywords")
        x = x.strip()
        if not x:
            continue
        out.append(x)

    if not out:
        raise Exception("Unparsable list of unsafe keywords")

    return set(out)


def _get_unsafe_attr_calls() -> set[tuple[str, str]]:
    cfg = get_cfg_value("safety.unsafe_attr_calls", list)

    out = []
    for pair in cfg:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or not isinstance(pair[0], str)
            or not isinstance(pair[1], str)
        ):
            raise Exception("Unparsable list of unsafe attribute calls")

        mod = pair[0].strip()
        attr = pair[1].strip()
        if not mod or not attr:
            continue
        out.append((mod, attr))

    if not out:
        raise Exception("Unparsable list of unsafe attribute calls")

    return set(out)


def code_is_not_safe(code_snippet: str) -> bool:
    """
    Analyze the code snippet for unsafe patterns using AST.
    Returns True if unsafe constructs are detected or on parse errors.
    """
    words = re.split(r"\W+", code_snippet)
    unsafe_keywords = _get_unsafe_keywords()
    if any(x in unsafe_keywords for x in words):
        return True

    unsafe_attr_calls = _get_unsafe_attr_calls()
    for x, y in unsafe_attr_calls:
        if x in words and y in words:
            return True

    return False
