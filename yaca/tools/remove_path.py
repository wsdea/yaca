import glob
import os
import shutil

from ..llm import FailedToolResult, SuccessToolResult
from .safety import is_path_allowed


def remove_path_tool(agent, glob_pattern: str):
    """
    Delete all files and directories that match ``glob_pattern``.

    Args:
        - glob_pattern (str) : A glob pattern (e.g., ``'tmp/**/*.log'``) that will be expanded relative to the project root. The pattern may match files,
        directories, or both.
    """
    # Resolve the pattern to absolute paths
    try:
        matched_paths = glob.glob(glob_pattern, recursive=True)
    except Exception as exc:
        return FailedToolResult(f"Invalid glob pattern: {exc}")

    if not matched_paths:
        return FailedToolResult(f"No paths matched the pattern '{glob_pattern}'.")

    # Filter out paths that are not allowed (e.g., ignored by .gitignore)
    disallowed = [p for p in matched_paths if not is_path_allowed(p)]
    if disallowed:
        return FailedToolResult(
            f"Removal aborted: some paths are disallowed: {disallowed}"
        )

    for path in matched_paths:
        # Preserving relative structure inside recycle bin
        rel_path = os.path.normpath(path)
        dest_path = os.path.join(agent.RECYCLE_BIN, rel_path)

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        shutil.move(path, dest_path)
        # removing it from open files
        agent.open_files = [
            x for x in agent.open_files if os.path.abspath(x) != os.path.abspath(path)
        ]

    return SuccessToolResult(
        f"Successfully removed {len(matched_paths)} matching path(s)"
    )
