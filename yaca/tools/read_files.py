from ..config import get_cfg_value
from ..llm import SuccessToolResult
from .safety import is_path_allowed


def read_files_tool(agent, files: list[str]):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Reads the content of up to {} files. You are encouraged to read multiple files at once for efficiency purposes.

    Args:
        - files (str): The path of the files to read.
    """
    max_files = get_cfg_value("tools.read_files.max_files_to_read", int)

    out = read_files_limited(files, max_files)
    out = f"<read_files_answer>\n{out}\n</read_files_answer>"
    return SuccessToolResult(out)


def read_files_limited(files, max_files):
    message = ""
    n = len(files)
    if n == 0:
        return "Provide a list of files to read"

    if n > 5:
        message += f"Warning, only showing the first {max_files} files of your list"
        files = files[:max_files]

    for f in files:
        if not is_path_allowed(f):
            # Skip disallowed paths with an error message
            content = f"\\nError reading {f} (Path not allowed)"
        else:
            try:
                content = read_file(f)
            except (FileNotFoundError, PermissionError) as e:
                content = f"\\nError reading {f} ({e!r})"

        if not content.strip():
            content = "(empty file, use the create_file to overwrite it if needed)"

        message += f"\n<content file={f}>{content}</content>"

    return message


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def add_file_to_relevant_file_tool(agent, files: list[str]):
    return SuccessToolResult("Success")
