from ..llm import AssistantResponse


def cannot_do_tool(agent, message: str):
    """Tool to use when you realized you cannot do the coding task as expected. Write a message explaining 1) what you have managed to do, 2) what's blocking you from finishing the task. Do not suggest ways to solve the issue.

    Args:
        - message (str): Message to send to the user.
    """
    return AssistantResponse(message)
