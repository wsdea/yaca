from ..llm import SuccessToolResult


def cannot_do_tool(agent, message: str):
    """Tool to use when you realized you cannot do the coding task as expected. Write a message explaining what you have done, and what's blocking you from finishing the task.

    Args:
        - message (str): Message to send to the user.
    """
    return SuccessToolResult(message)
