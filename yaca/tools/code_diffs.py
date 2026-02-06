import os
import re

from ..llm import FailedToolResult, SuccessToolResult
from .read_files import read_file
from .safety import code_is_not_safe, is_path_allowed, set_unsafe_tripped
from .sanitize import clean_string


def search_replace_diff_tool(
    agent,
    file_path: str,
    search_text: str,
    replace_text: str,
    indent_string: str = "",
    allow_multiple_matches: bool = False,
):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """
    Function to modify a file by searching a ``search_text`` in the file at ``file_path`` and replace it with ``replace_text``.

    Args:
        - file_path (str): Path to the file to be modified.
        - search_text (str) : Full text to search that will be replaced.
        - replace_text (str) : Text that will replace each occurrence of ``search_text``.
        - indent_string (str, default ``''``): If non‑empty, each line of ``replace_text`` will be prefixed with this string before replacement.
        - allow_multiple_matches (bool, default ``False``): For most usecases, keep as False. If ``True`` all occurrences are replaced. If ``False`` and more than one occurrence is found, the function returns an error.
    """
    if file_path not in agent.open_files or not is_path_allowed(file_path):
        return FailedToolResult(f"Path not allowed: {file_path}")
    if not os.path.exists(file_path):
        return FailedToolResult(f"Target file does not exist: {file_path}")

    if code_is_not_safe(replace_text):
        agent.logger.debug(f"UNSAFE CODE GENERATED, DISABLING TESTS\n{replace_text}")
        set_unsafe_tripped()

    content = read_file(file_path)

    match_count = content.count(search_text)

    if match_count == 0:
        # No occurrence – nothing to replace
        return FailedToolResult("No matches found; file left unchanged.")

    if match_count > 1 and not allow_multiple_matches:
        return FailedToolResult(
            f"Multiple ({match_count}) matches found; Increase the size of the text to search or set allow_multiple_matches=True to replace all"
        )

    # Perform the replacement
    if indent_string:
        replace_lines = replace_text.splitlines()
        ends_with_newline = replace_text.endswith("\n")
        indented = "\n".join(f"{indent_string}{line}" for line in replace_lines)
        if ends_with_newline:
            indented += "\n"
        replace_to_use = indented
    else:
        replace_to_use = replace_text

    replace_to_use = clean_string(replace_to_use)
    new_content = content.replace(search_text, replace_to_use)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return SuccessToolResult(f"Replaced {match_count} occurrence(s) in {file_path}.")


def apply_diff_tool(agent, file_path: str, diffs: str = ""):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """
    Applies diffs to the given file. Use this to perform edits on an existing file.
    Follow this diff format:
    ```
    <apply_diff>
    <file_path>filename.py</file_path>
    <diffs>
    <diff_search_1>[exact code line
    or block to find
    including whitespace]</diff_search_1>
    <diff_replace_1>[new content to replace with]</diff_replace_1>

    <diff_search_2>[exact code line
    or block to find including whitespace]</diff_search_2>
    <diff_replace_2>[new content to replace with]</diff_replace_2>
    ...
    </diffs>
    </apply_diff>

    Careful, make sure your diff blocks do not overlap with each other. Make sure to put the text as seen by a human in a code editor, no escaping or "&quot;" sheenanigans.
    ```
    Args:
        file_path (str): Path to the file to be modified.
        diffs (str): The search/replace blocks defining the changes.
    """
    if not is_path_allowed(file_path):
        return FailedToolResult(f"Path not allowed: {file_path}")
    if not os.path.exists(file_path):
        return FailedToolResult(f"Target file does not exist: {file_path}")

    if not diffs:
        return FailedToolResult("diff text is empty")

    # uses search_replace
    # Parse diff blocks
    search_pattern = re.compile(r"<diff_search_(\d+)>(.*?)</diff_search_\1>", re.DOTALL)
    replace_pattern = re.compile(
        r"<diff_replace_(\d+)>(.*?)</diff_replace_\1>", re.DOTALL
    )

    searches = [(int(m.group(1)), m.group(2)) for m in search_pattern.finditer(diffs)]
    replaces = [(int(m.group(1)), m.group(2)) for m in replace_pattern.finditer(diffs)]

    if not searches:
        return FailedToolResult("No diff_search blocks found. Try smaller blocks")

    if len(searches) != len(replaces):
        return FailedToolResult("Mismatched number of search and replace blocks")

    # Ensure ordering by index
    searches.sort(key=lambda x: x[0])
    replaces.sort(key=lambda x: x[0])

    for (s_idx, search_text), (r_idx, replace_text) in zip(searches, replaces):
        if s_idx != r_idx:
            return FailedToolResult(
                f"Non-matching diff block indices: search {s_idx} vs replace {r_idx}"
            )

        result = search_replace_diff_tool(
            agent, file_path, search_text, replace_text, allow_multiple_matches=False
        )
        if isinstance(result, FailedToolResult):
            return result

    return SuccessToolResult(f"Applied {len(searches)} diff block(s) to {file_path}")
