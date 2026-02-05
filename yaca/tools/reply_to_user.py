from ..llm import SuccessToolResult


def reply_to_user_tool(agent, message: str):
    """Tool to use when you want to directly talk to the user. Do not include code blocks in your message unless explicitely asked by the user. Use markdown formatting. Use clickable links when citing files.

    Args:
        - message (str): The message to display.
    """
    return SuccessToolResult(message)
