import os
import re

from ..config import get_cfg_value
from ..llm import FailedToolResult, SuccessToolResult, find_json
from .list_files import list_files
from .open_files import open_files_tool
from .prompt_loader import PromptLoader
from .read_files import read_file


prompt_loader = PromptLoader(prompt_folder=os.path.dirname(__file__))


def search_tool(
    agent,
    glob_pattern: str,
    pattern: str,
    reason: str,
    max_files: int = 10,
):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """
    Searches for a regex pattern inside glob files and update the open files with the search results.

    Args:
        - glob_pattern (str): Pattern to be fed into recursive glob.glob for searching. eg. './folder/**'
        - pattern (str): Python regex pattern to search for inside the files.
        - reason (str): Explain why you need to execute this search. Say what you already know and what you need to know.
    """
    results = search_raw(glob_pattern=glob_pattern, pattern=pattern)

    if isinstance(results, FailedToolResult):
        return results

    if results.txt.startswith("No result"):
        return results

    prompt = prompt_loader(
        "search_reply_prompt", REQUEST=reason, SEARCH_RESULTS=results.txt
    )
    res = agent.llm(prompt)
    res = find_json(res)

    if not isinstance(res, dict):
        return FailedToolResult("Search error")

    new_files = res.get("relevant_files")
    if new_files:
        if len(new_files) > max_files:
            agent.logger.debug(
                f"Warning, too many files in the search, opening the first {max_files}"
            )
            new_files = new_files[:max_files]

        open_files_tool(agent, new_files)
        return SuccessToolResult(
            f"Search automatically opened the following files for you: {', '.join(new_files)}."
        )

    return SuccessToolResult("No relevant files found in the search")


def search_raw(
    glob_pattern: str,
    pattern: str,
    context_lines: int = 2,
):
    if not pattern:
        return FailedToolResult("pattern needs to be a non empty string")

    try:
        regex = re.compile(pattern, flags=re.IGNORECASE)
    except re.error as e:
        return FailedToolResult(f"Invalid regex pattern: {e}")

    # First we obtain the list of matching files using the existing tool
    files = list_files(glob_pattern, ignore_patterns=None)
    if not files:
        return FailedToolResult(f"No files found with {glob_pattern=}")

    # Search each file and collect snippets with context lines
    snippets: list[str] = []
    for file_path in files:
        if not os.path.isfile(file_path):
            continue

        # for each file, we gather matched lines, overlapping ones are merged
        lines = read_file(file_path).splitlines()
        matched_lines = ["X"] * len(lines)

        for idx, line in enumerate(lines):
            if regex and regex.search(line):
                start = max(idx - context_lines, 0)
                end = min(idx + context_lines + 1, len(lines))
                for i in range(start, end):
                    matched_lines[i] = "O"

        # groups that are close will still get merged
        matched_lines = "".join(matched_lines)

        # creating groups of lines
        file_snippets = [[]]
        for i, (line, symbol) in enumerate(zip(lines, matched_lines)):
            if symbol == "O":
                # we append the lines to the group
                file_snippets[-1].append((i, line))
            else:
                if len(file_snippets[-1]) > 0:
                    # we create a new group
                    file_snippets.append([])

        # building contexts
        for line_list in file_snippets:
            if len(line_list) == 0:
                continue

            line_numbers = [x[0] for x in line_list]
            line_list = [x[1] for x in line_list]

            start = min(line_numbers)
            end = max(line_numbers)

            context = "\n".join(line_list)
            start_string = "[...]\n" if start > 0 else ""
            end_string = "\n[...]" if end < len(lines) - 1 else ""

            snippets.append(
                f"<result file={file_path}>\n{start_string}{context}{end_string}\n</result>\n"
            )

    max_results = get_cfg_value("tools.search.max_results")
    if not isinstance(max_results, int) or max_results <= 0:
        max_results = 30

    if len(snippets) > max_results:
        message = f"Warning, search truncated to {max_results} results. Improve your query next time.\n"
        snippets = snippets[:max_results]
    else:
        message = ""

    if snippets:
        message += "\n".join(snippets)
        return SuccessToolResult(f"<search_results>\n{message}\n</search_results>")

    return FailedToolResult(f"No result with {pattern=}")
