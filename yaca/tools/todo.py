import json
import os

from ..llm import FailedToolResult, SuccessToolResult, find_json
from .open_files import open_files_tool
from .prompt_loader import PromptLoader

MAX_RESULTS = 30
TODO_STATUSES = ["pending", "done"]

prompt_loader = PromptLoader(prompt_folder=os.path.dirname(__file__))
""


def validate_todo(agent, todo: list[str], user_request: str) -> str:
    """
    Returns an empty string if the todo is fine, otherwise returns an error message
    """
    assert isinstance(todo, list), "Todo should be a list of str"

    todo_txt = ""
    for x in todo:
        todo_txt += f"\n- {x}"

    prompt = prompt_loader(
        "todo_check_prompt",
        TODO=todo_txt.strip(),
        USER_REQUEST=user_request.strip(),
    )
    res = agent.llm(prompt)
    dic = find_json(res)

    if not isinstance(dic, dict):
        agent.logger.debug(f"WARNING, LLM response is not JSON :\n{dic}")
        return ""

    if dic.get("todo_is_ok"):
        return ""

    return dic.get("explaination") or "Double check TODO rules"


def start_coding_task_tool(
    agent,
    task_name: str,
    user_request: str,
    relevant_files: list[str],
    todo_list: list[str],
):
    """
    Tool to call when you have enough context to start coding. Write a todo list of what to do. The todo list must only contain coding tasks such as creating, editing or deleting coding files. The todo list must not include tasks such as searching for relevant files, understanding the codebase, etc. Do not add tests, except when specifically asked to. Do not include code blocks.

    Args:
        - task_name (str) : Short title for the task
        - user_request (str) : Message of the user
        - relevant_files (list[str]) : List of files to open or create to solve this task
        - todo_list (list[str]) : Ordered list of items to do
    """
    if not relevant_files:
        return FailedToolResult("No relevant_files list is empty")

    if len(relevant_files) > 5:
        return FailedToolResult(
            "Too many relevant files. Split your task into multiple subtasks, and run this tool again with the first sub task."
        )

    error = validate_todo(agent, todo_list, user_request)

    if error:
        return FailedToolResult(
            "Error creating with the todo. Explaination :\n"
            f"{error}\n"
            "Call other tools to gather more information or update the todo."
        )

    todo_list = [{"item": x, "status": "pending"} for x in todo_list]

    from ..agents.coder.main import YacaCoder

    coder = YacaCoder(todo_list=todo_list, _pytest=agent._pytest)

    open_files_tool(coder, relevant_files, overwrite=True, discard_non_existing=False)

    assert len(coder.open_files) > 0
    agent.logger.debug(
        f"Running coding agent with \nopen_files={coder.open_files}\ntodo_list={coder.todo_list}\nlast_list_files={coder.last_list_files}"
    )

    result = agent.run_subagent(
        name=task_name,
        agent=coder,
        run_kwargs={"user_message": coder.prompt_loader("code_mode_start")},
    )

    if result.tool_name == "cannot_do":
        agent.logger.debug(f"Coding task could be done:{result.txt}")
        return FailedToolResult(
            f"Coding task could not be done properly. Here is an explaination from the coder :\n{result.txt}"
        )

    agent.logger.debug(f"Coding task done:{result.txt}")

    return SuccessToolResult(
        f"Coding task is done, here is the summary :\n{result.txt}\nUse the tool to ask a question. In the message, first repeat what has been done in all the previous coding tasks so far, and then ask **one** follow-up question suggesting what to do next."
    )


def update_todo_tool(agent, todo_list: str):
    """Tool to create or update the todo list.

    Args:
        - todo_list (list[dict]) : Ordered list of dict with keys 'item' and 'status'. Statuses can only be 'pending' or 'done'."""
    try:
        todo = json.loads(todo_list)
        assert isinstance(todo, list)
        todo = [{"status": x["status"], "item": x["item"]} for x in todo]
    except (AssertionError, json.JSONDecodeError, KeyError):
        return FailedToolResult(
            "Todo should be a json list of dicts with keys and 'item' and 'status"
        )

    agent.todo_list = todo

    return SuccessToolResult("Todo list successfully updated")
