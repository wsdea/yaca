import os

from ..llm import FailedToolResult, SuccessToolResult
from .safety import is_path_allowed


def create_folder_tool(agent, path: str):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """
    Creates an empty folder at the specified path.

    Args:
        - path (str): The directory path to create. If the folder already exists, nothing happens.
    """
    if not is_path_allowed(path):
        return FailedToolResult(f"Path not allowed: {path}")

    create_folder(path)
    return SuccessToolResult(f"Folder '{path}' created (or already existed).")


def create_folder(path: str):
    os.makedirs(path, exist_ok=True)
