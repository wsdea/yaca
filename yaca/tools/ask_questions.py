import os

from ..llm import AssistantResponse, FailedToolResult, find_json
from .prompt_loader import PromptLoader

prompt_loader = PromptLoader(prompt_folder=os.path.dirname(__file__))


def validate_questions(agent, questions: str) -> str:
    """
    Returns an empty string if the questions are fine, otherwise returns an error message
    """
    prompt = prompt_loader(
        "ask_questions_check_prompt",
        QUESTIONS=questions,
    )
    res = agent.llm(prompt)
    dic = find_json(res)

    if not isinstance(dic, dict):
        agent.logger.debug(f"WARNING, LLM response is not JSON :\n{dic}")
        return ""

    if dic.get("message_is_valid"):
        return ""

    return dic.get("explaination") or "Double check question rules"


def ask_questions_tool(agent, message: str):
    # Do not change the docstring as it's imported for tool calling, do not remove this comment
    """Tool to use when you need clarification about what the user wants or after coding to ask a follow-up question. Only use this tool after you already tried understanding the user's intent with other tools such as file reading, search, etc. Use markdown formatting. Use clickable links when citing files.

    Args:
        - message (str): The message to display. It can consist of multiple questions. If so, give a number to each questions. For each question, propose 2-4 answers (give them a letter).
    """

    error = validate_questions(agent, message)

    if error:
        return FailedToolResult(
            f"Cannot ask these questions. Here is an explaination why :\n{error}"
        )

    return AssistantResponse(message)
