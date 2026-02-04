import os

from ..llm import FailedToolResult, SuccessToolResult, find_json
from .safety import is_path_allowed


def open_files_tool(agent, files: list[str], overwrite: bool = False):
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
        if not (
            os.path.isfile(x)
            and os.path.exists(x)
            and x not in new_files
            and os.path.abspath(x) not in new_files
        ):
            continue

        if is_path_allowed(x):
            new_files.append(x)
        else:
            errors.append(f"{x!r} doesn't exist or you are not allowed to see it")

    if overwrite:
        agent.open_files = sorted(set(new_files))
    else:
        agent.open_files = sorted(set(agent.open_files) | set(new_files))

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
