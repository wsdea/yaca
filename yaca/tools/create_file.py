import os

from ..llm import FailedToolResult, SuccessToolResult
from .open_files import open_files_tool
from .safety import code_is_not_safe, is_path_allowed
from .sanitize import clean_string


def create_file_tool(agent, path: str, content: str):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Creates or overwrites a file at the given path with the provided content. Use it to create or rewrite a file from scrath. It will automatically create the parent folders. Do not use this tool for small edits, use search_other tools instead.

    Args:
        - path (str): The filesystem path where the file will be created or overwritten.
        - content (str): The text content to write into the file.
    """
    if path not in agent.open_files or not is_path_allowed(path):
        return FailedToolResult(f"Path not allowed: {path}")

    if code_is_not_safe(content):
        agent.logger.debug(f"UNSAFE CODE GENERATED, DISABLING TESTS\n{content}")
        agent.disable_run_command = True

    create_file(path, content)
    if not os.path.exists(path):
        return FailedToolResult("Error creating file")

    open_files_tool(agent, [path], overwrite=False)
    return SuccessToolResult(f"{path} has been written to and added to open files.")


def create_file(path: str, content: str):
    content = clean_string(content)
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
