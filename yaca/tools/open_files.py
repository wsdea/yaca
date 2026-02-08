import os

from ..llm import FailedToolResult, SuccessToolResult, find_json
from .safety import is_path_allowed


def open_files_tool(
    agent,
    files: list[str],
    overwrite: bool = False,
    discard_non_existing=True,
):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Tool to update currently open files in the editor. Please list **all** the files you need to open. Files outside of this list will be **closed**

    Args:
        - files (list[str]) : list of all paths relative to the project of the files to be opened in the editor. All other files won't be opened.
    """
    if not files:
        return FailedToolResult("No files were provided")

    new_files = []
    errors = []
    for x in files:
        abs_x = os.path.abspath(x)

        if not is_path_allowed(abs_x):
            errors.append(f"{abs_x!r} is not allowed")
            continue

        if not os.path.exists(abs_x):
            if discard_non_existing:
                continue
            new_files.append(abs_x)
            continue

        if os.path.isfile(abs_x):
            new_files.append(abs_x)

    new_files = set([os.path.relpath(x, agent.CWD) for x in new_files])

    if overwrite:
        agent.open_files = sorted(new_files)
    else:
        agent.open_files = sorted(set(agent.open_files) | new_files)

    if errors:
        return FailedToolResult("\n".join(errors))

    return SuccessToolResult("Open files were modified successfully")


def find_files_to_open(agent):
    prompt = agent.prompt_loader(
        "files_to_open", CONVERSATION=agent.conversation_context()
    )
    response_to_user = agent.llm(prompt)
    dic = find_json(response_to_user)
    if not isinstance(dic, dict):
        agent.logger.debug(f"Wrong LLM answer :\n{response_to_user}")
        return

    files = dic.get("files_to_open", [])
    files_to_create = dic.get("files_to_create", [])
    agent.open_files_tool(files)

    if len(agent.open_files) == 0 and not files_to_create:
        agent.logger.debug(
            "Warning, no open or to create files, coder will probably be lost"
        )
