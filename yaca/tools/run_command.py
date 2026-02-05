import subprocess

from ..llm import FailedToolResult, SuccessToolResult


def _normalizing_output(data):
    """Normalizing subprocess output into clean string form"""

    if not data:
        return ""

    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")

    return data.rstrip("\r\n")


def run_command_tool(agent, cmd: str, timeout: int = 120):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Runs a command in the user terminal from the current working directory

    Args:
        - cmd (str) : String for the command.
    """

    if agent.disable_run_command:
        # Pretending command being executed successfully
        return SuccessToolResult("Success")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,  # return stdout/err as strings
            timeout=timeout,
            check=False,  # we'll raise our own CommandError if needed
        )

    except subprocess.TimeoutExpired as e:
        message = f"Command {cmd} timed out after {timeout} seconds."

        stdout_txt = _normalizing_output(e.stdout)
        stderr_txt = _normalizing_output(e.stderr)

        if stdout_txt:
            message += f"\n<stdout>\n{stdout_txt}\n</stdout>"

        if stderr_txt:
            message += f"\n<stderr>\n{stderr_txt}\n</stderr>"

        return FailedToolResult(message)

    except Exception as e:
        message = f"Command {cmd} failed to run: {e}."
        return FailedToolResult(message)

    success = result.returncode == 0

    message = (
        f"Command {cmd} executed {'successfully' if success else 'with failure(s)'}."
    )

    stdout_txt = _normalizing_output(result.stdout)
    stderr_txt = _normalizing_output(result.stderr)

    if stdout_txt:
        message += f"\n<stdout>\n{stdout_txt}\n</stdout>"

    if stderr_txt:
        message += f"\n<stderr>\n{stderr_txt}\n</stderr>"

    if success:
        return SuccessToolResult(message)

    return FailedToolResult(message)
