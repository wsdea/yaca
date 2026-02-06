import glob
import os

from ..config import get_cfg_value
from ..llm import FailedToolResult, SuccessToolResult
from .safety import (
    DOTSEP,
    _compile_ignore_rules,
    _is_ignored,
    _load_gitignore,
    default_ignores,
)


def common_prefix_folder(paths: list[str]) -> str:
    """
    Return the deepest common directory shared by all given file system paths.

    The function normalises each path, computes the common path using
    :func:`os.path.commonpath`, and ensures the result corresponds to a
    directory (i.e., it does not truncate a partial folder name).

    Parameters
    ----------
    paths : List[str]
        A list of file system paths.

    Returns
    -------
    str
        The common directory path. Returns an empty string if the input list
        is empty or there is no common directory.
    """
    if not paths:
        return ""
    normalized = [os.path.normpath(p) for p in paths]
    try:
        common = os.path.commonpath(normalized)
    except ValueError:
        return ""
    if not os.path.isdir(common):
        common = os.path.dirname(common)
    return common


def list_files(glob_pattern, ignore_patterns):
    assert isinstance(glob_pattern, str)
    ignore_patterns = ignore_patterns or []
    assert isinstance(ignore_patterns, list)
    glob_pattern = glob_pattern or "./**"

    # forcing local paths
    glob_pattern = DOTSEP + glob_pattern.removeprefix(DOTSEP)

    git_rules = _load_gitignore()
    all_rules = _compile_ignore_rules(ignore_patterns, default_ignores(), git_rules)

    matched_files = glob.glob(glob_pattern, recursive=True, include_hidden=True)
    # removing ./ prefix
    matched_files = [f.removeprefix(DOTSEP) for f in matched_files]

    # collecting matching files
    matched_files = [
        f for f in matched_files if os.path.isfile(f) and not _is_ignored(f, all_rules)
    ]
    return matched_files


def list_files_tool(agent, glob_pattern: str, return_message: bool = True):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Returns a tree representation string of files and folders in `path` respecting search patterns. Note files in .gitignore will be ignored.

    Args:
        - glob_pattern (str) : Patterns to be fed into recursive glob.glob for searching. eg. './folder/**'
    """
    if not glob_pattern:
        return FailedToolResult("glob_pattern is empty")

    max_depth = get_cfg_value("tools.list_files.max_depth")
    if max_depth <= 0:
        return FailedToolResult("Incorrect max_depth")

    matched_files = list_files(glob_pattern, ignore_patterns=None)

    common_prefix = common_prefix_folder(matched_files)
    if len(common_prefix) == 0:
        current_depth = 0
    else:
        current_depth = len(common_prefix.split(os.sep))

    # applying max depth
    matched_files = [
        os.path.join(*(x.split(os.sep)[: current_depth + max_depth]))
        for x in matched_files
    ]
    matched_files = list(set(matched_files))

    # adding fake files listing number of items for folders that were hidden by max_depth
    new_files = []
    for x in matched_files:
        if os.path.isdir(x):
            number_of_items = len(os.listdir(x))
            if number_of_items > 0:
                new_files.append(
                    os.path.join(x, f"<{number_of_items} hidden items...>")
                )
            else:
                new_files.append(os.path.join(x, "<empty folder>"))
        else:
            new_files.append(x)

    # building tree
    tree = {}
    for f in new_files:
        parts = f.split(os.sep)

        node = tree
        for p in parts[:-1]:  # directories
            node = node.setdefault(p, {})
        node.setdefault("__files__", []).append(parts[-1])

    # rendering tree
    def render(node, indent_level=0):
        lines = []
        indent = "  " * indent_level

        # rendering folders
        for key in sorted(k for k in node.keys() if k != "__files__"):
            lines.append(f"{indent}- {key}/")
            lines.extend(render(node[key], indent_level + 1))

        # rendering files
        if "__files__" in node:
            for f in sorted(node["__files__"]):
                lines.append(f"{indent}- {f}")

        return lines

    message = "\n".join(render(tree))

    if return_message:
        message = f"<list_files_result>\n{message}\n</list_files_result>"
        return SuccessToolResult(message)

    return SuccessToolResult(message)
