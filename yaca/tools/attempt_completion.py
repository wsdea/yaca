import ast

from ..llm import AssistantResponse, FailedToolResult, SuccessToolResult
from .read_files import read_file


def validate_python_syntax(files):
    """
    Walk through all .py files under ``files`` and try to parse them with ``ast.parse``.
    Returns a SuccessToolResult if all files parse, otherwise a FailedToolResult containing
    all syntax errors joined by '; '.
    """
    py_files = [x for x in files if x.endswith(".py")]
    errors: list[str] = []
    for py_file in py_files:
        try:
            source = read_file(py_file)
            ast.parse(source, filename=str(py_file))
        except SyntaxError as exc:
            errors.append(f"Syntax error in {py_file}: {exc.msg}")

    if errors:
        return FailedToolResult("; ".join(errors))

    return SuccessToolResult("All Python files have valid syntax.")


def attempt_completion_tool(agent, recap: str):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Function to call when you consider the user's request to be fully done. This function will run some checks, lint, run tests and return a message about the success of this.

    Args:
        recap (str): Quick recap of what you have done, including stuff that was in the todo list. Do not mention the todo though. Mention edited or created files. No code block. Use markdown and bullet points.
    """

    if "?" in recap:
        return FailedToolResult(
            "Task recap cannot be a question. Use other tools for that."
        )

    # First, validate Python syntax before linting
    syntax_result = validate_python_syntax(agent.open_files)
    if isinstance(syntax_result, FailedToolResult):
        return FailedToolResult(f"{syntax_result.txt}. Syntax validation failed.")

    # Then we check all items of the todo are done
    for x in agent.todo_list:
        if x["status"] != "done":
            return FailedToolResult("Finish the tasks of the todo list.")

    return AssistantResponse(recap)
