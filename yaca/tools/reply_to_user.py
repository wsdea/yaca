from ..llm import AssistantResponse


def reply_to_user_tool(agent, message: str):
    """Tool to use when you want to directly talk to the user. This can be if you cannot complete the taask given, and need additionnal context. Include details if needed.

    Args:
        - message (str): The message to display.
    """
    return AssistantResponse(message)
