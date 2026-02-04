import subprocess

from ..llm import FailedToolResult, SuccessToolResult


def run_command_tool(agent, cmd: str, timeout: int = 120):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Runs a command in the user terminal from the current working directory

    Args:
        - cmd (str) : String for the command.
    """

    if agent.disable_run_command:
        # we pretend the command was done successfully, but it was not
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
        if e.stdout:
            txt = e.stdout.rstrip("\r\n")
            message += f"\n<stdout>\n{txt}\n</stdout>"
        if e.stderr:
            txt = e.stderr.rstrip("\r\n")
            message += f"\n<stderr>\n{txt}\n</stderr>"
        return FailedToolResult(message)
    except Exception as e:
        message = f"Command {cmd} failed to run: {e}."
        return FailedToolResult(message)

    success = result.returncode == 0

    if success:
        message = "successfully"
    else:
        message = "with failure(s)"

    message = f"Command {cmd} executed {message}."
    if result.stdout:
        txt = result.stdout.rstrip("\r\n")
        message += f"\n<stdout>\n{txt}\n</stdout>"

    if result.stderr:
        txt = result.stderr.rstrip("\r\n")
        message += f"\n<stderr>\n{txt}\n</stderr>"

    if success:
        return SuccessToolResult(message)

    return FailedToolResult(message)
