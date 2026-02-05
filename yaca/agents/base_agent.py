import logging
import os
import sys
import threading
import uuid

from ..llm import LLMClient
from ..llm.messages import (
    AssistantResponse,
    AttemptedToolCall,
    FailedToolCall,
    FailedToolResult,
    HelperMessage,
    Message,
    UserInput,
)
from ..logger import get_logger
from ..tools.ask_questions import ask_questions_tool
from ..tools.attempt_completion import attempt_completion_tool
from ..tools.code_diffs import apply_diff_tool
from ..tools.create_file import create_file_tool
from ..tools.hooks import HookCaller
from ..tools.list_files import list_files_tool
from ..tools.open_files import open_files_tool
from ..tools.prompt_loader import PromptLoader
from ..tools.remove_path import remove_path_tool
from ..tools.reply_to_user import reply_to_user_tool
from ..tools.search import search_tool
from ..tools.todo import start_coding_task_tool, update_todo_tool
from ..tools.tool_caller import ToolCaller, ToolParsingError


class BaseAgent:
    def __init__(
        self,
        _pytest: bool = False,
        llm_debug_folder: str | None = None,
        llm_cache_folder: str | None = None,
    ) -> None:
        """Initialize the agent and wire up tools, logging, and LLM client.

        Args:
            _pytest: Whether the agent is running under pytest (adjusts tool set).
            llm_debug_folder: Folder where raw LLM exchanges can be logged.
            llm_cache_folder: Folder used to cache LLM responses.
        """
        self.id = str(uuid.uuid4())
        self.name = self.__class__.__name__
        self.logger = get_logger(__name__)
        self.logger.debug("__init__ start")
        self._pytest = _pytest
        self.disable_run_command = False
        self.is_running = False
        self._cancel_event = threading.Event()
        self.status_message = ""
        self.running_subagents = {}

        self.DOT_YACA_FOLDER = os.path.join(os.getcwd(), ".yaca")
        self.STATE_FOLDER = os.path.join(self.DOT_YACA_FOLDER, ".state")
        os.makedirs(self.STATE_FOLDER, exist_ok=True)

        self.RECYCLE_BIN = os.path.join(self.DOT_YACA_FOLDER, "recycle_bin")
        os.makedirs(self.RECYCLE_BIN, exist_ok=True)
        self.logger.debug(f"{self.name} RECYCLE_BIN=%s", self.RECYCLE_BIN)

        self.AGENT_STATE_FOLDER = os.path.join(self.STATE_FOLDER, self.name)
        os.makedirs(self.AGENT_STATE_FOLDER, exist_ok=True)
        # dir of the subclass
        self.AGENT_FOLDER = os.path.dirname(
            sys.modules[self.__class__.__module__].__file__
        )
        os.makedirs(self.AGENT_FOLDER, exist_ok=True)

        self.DEBUG_FILE = os.path.join(self.AGENT_STATE_FOLDER, "debug.log")

        self._setup_debug_file_logging()

        self.llm = LLMClient(
            llm_debug_folder=llm_debug_folder
            or os.path.join(self.AGENT_STATE_FOLDER, "llm_debug"),
            llm_cache_dir=llm_cache_folder
            or os.path.join(self.STATE_FOLDER, "llm_cache"),
        )

        self.prompt_loader = PromptLoader(self.AGENT_FOLDER)

        hook_caller = HookCaller(os.path.join(self.DOT_YACA_FOLDER, "hooks.yaml"))
        self.tool_caller = ToolCaller(
            {
                "open_files": open_files_tool,
                "list_files": list_files_tool,
                "search": search_tool,
                "reply_to_user": reply_to_user_tool,
                "ask_questions": ask_questions_tool,
                "start_coding_task": start_coding_task_tool,
                "update_todo": update_todo_tool,
                "apply_diff": apply_diff_tool,
                "create_file": create_file_tool,
                "remove_path": remove_path_tool,
                "attempt_completion": attempt_completion_tool,
            },
            hook_caller=hook_caller,
        )
        # tools that can only be called when they are the first tool to call in the xml
        self.has_to_be_first = [
            "update_todo",
            "start_coding_task",
            "ask_questions",
        ]
        for x in self.has_to_be_first:
            assert x in self.tool_caller.ALL_TOOLS

        self.last_result_txt = ""
        self.reset_conversation()
        self.logger.debug("__init__ done")

    def log(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def _setup_debug_file_logging(self) -> None:
        """Ensure a debug file handler is configured for the `yaca` logger."""
        base_logger = logging.getLogger("yaca")
        base_logger.setLevel(logging.DEBUG)

        for h in list(base_logger.handlers):
            if isinstance(h, logging.StreamHandler) and not isinstance(
                h, logging.FileHandler
            ):
                base_logger.removeHandler(h)

        existing_file_handlers = [
            h
            for h in base_logger.handlers
            if isinstance(h, logging.FileHandler)
            and getattr(h, "baseFilename", None) == os.path.abspath(self.DEBUG_FILE)
        ]
        if len(existing_file_handlers) == 1:
            return

        for h in list(base_logger.handlers):
            if isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None):
                if os.path.abspath(h.baseFilename) == os.path.abspath(self.DEBUG_FILE):
                    base_logger.removeHandler(h)

        # resetting the debug file
        open(self.DEBUG_FILE, "w", encoding="utf-8").close()

        file_handler = logging.FileHandler(self.DEBUG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s"
            )
        )
        base_logger.addHandler(file_handler)

        self.logger.debug(
            f"{self.name} debug file logging enabled path=%s", self.DEBUG_FILE
        )

    def run_subagent(self, name: str, agent, run_kwargs) -> None:
        """Run a subagent and wait for the result"""
        if run_kwargs is None:
            run_kwargs = {}

        if not isinstance(run_kwargs, dict):
            raise TypeError("run_kwargs must be a dict")

        name = f"{name} [{str(uuid.uuid4()).split('-')[0]}]"
        self.status_message = f"Running subagent {agent.name}"
        self.running_subagents[name] = agent
        try:
            return agent(**run_kwargs)
        finally:
            self.status_message = f"Subagent {agent.name} done"
            self.running_subagents.pop(name, None)

    def request_cancel(self) -> None:
        """Request cooperative cancellation of the current agent processing."""
        self._cancel_event.set()
        for agent in self.running_subagents.values():
            agent.request_cancel()

        self.running_subagents.clear()
        self.status_message = "Cancelled"

    def clear_cancel(self) -> None:
        """Clear the cancellation flag so processing can resume normally."""
        self._cancel_event.clear()

    @property
    def is_running(self):
        """Whether the agent is currently processing a user message."""
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        """Set the running status flag."""
        self._is_running = bool(value)

    # Conversation management
    def append_message(self, msg: Message, idx=None) -> None:
        """Append or insert a message into the conversation history."""
        assert isinstance(msg, Message)
        if not msg:
            return

        if idx is None:
            self.conversation.append(msg)
        else:
            self.conversation.insert(idx, msg)

    def reset(self) -> None:
        """Reset agent state (conversation, context) to defaults."""
        self.clear_cancel()
        self.status_message = "Waiting for user message"
        self.reset_conversation()

    def reset_conversation(self) -> None:
        """Reset the in-memory conversation history to an empty state."""
        self.logger.debug("reset_conversation")
        self.conversation = []
        self.last_result_txt = ""
        self.status_message = "Waiting for user message"

    # Context management
    def _trim_attempted_tool_calls(self) -> None:
        """Trim AttemptedToolCall messages to keep conversation compact."""
        attempted_tool_calls = [
            x for x in self.conversation if isinstance(x, AttemptedToolCall)
        ]
        if len(attempted_tool_calls) <= 1:
            return

        last_attempted_tool_call = attempted_tool_calls[-1]

        for msg in attempted_tool_calls[:-1]:
            if msg is last_attempted_tool_call:
                continue

            lines = msg.txt.splitlines()
            if len(lines) <= 6:
                continue

            msg.txt = "\n".join(lines[:3] + ["[..]"] + lines[-3:])

    def prepare_conversation(self) -> list[Message]:
        """Build the LLM-ready conversation, injecting helper context messages."""
        self.logger.debug("conversation_for_llm start")
        # cleaning helper messages
        # They may be added back by the subclass
        self.conversation = [
            x for x in self.conversation if not isinstance(x, HelperMessage)
        ]
        return self.conversation

    def set_tools(self, *tools: str) -> None:
        """Restrict which tools the LLM is allowed to call."""
        if self._pytest:
            tools = [x for x in tools if x != "ask_questions"]
        self.tool_caller.set_tools(tools)

    # Main loop
    def run(self, user_message: str) -> Message:
        """Process a user message until an assistant response is produced.

        This method:
        - Appends the user input to the conversation.
        - Calls the LLM to obtain XML tool calls.
        - Executes tools sequentially, appending tool results to the conversation.
        - Stops when a tool returns an assistant response or a fatal tool error.

        Args:
            user_message: Raw user message text.
        """
        self.logger.debug("process_user_message user_message_len=%s", len(user_message))
        self.append_message(UserInput(user_message))
        while True:
            if self._cancel_event.is_set():
                self.status_message = "Cancelled"
                self.logger.debug(f"{self.name} processing cancelled")
                self.last_result_txt = "Cancelled by user"
                return AssistantResponse("Cancelled by user")

            self.logger.debug(f"{self.name} calling LLM")
            llm_response = self.llm(self.prepare_conversation())
            self.logger.debug(f"{self.name} LLM response\n%s", llm_response)

            self.status_message = "Waiting for tool calls"
            try:
                tool_calls = self.tool_caller.text_to_kwargs(llm_response)
            except ToolParsingError as e:
                self.status_message = f"Tool parsing error ({e})"
                self.append_message(AttemptedToolCall(llm_response))
                self.append_message(FailedToolCall(f"Error : {e}"))
                self.logger.debug("Error parsing llm response: %s", e, exc_info=True)
                continue

            processed_tool_txt = ""
            processed_messages = []
            already_called = set()
            for i, (tool_name, kwargs, tool_txt) in enumerate(tool_calls):
                if self._cancel_event.is_set():
                    self.status_message = "Cancelled"
                    self.logger.debug(f"{self.name} processing cancelled")
                    self.last_result_txt = "Cancelled by user"
                    return AssistantResponse("Cancelled by user")

                if tool_name in already_called:
                    self.logger.debug(f"Skipping already called tool {tool_name}")
                    continue

                if i > 0 and tool_name in self.has_to_be_first:
                    self.logger.debug(
                        f"Agent tried to call {tool_name} as non first tool"
                    )
                    break

                self.logger.info("Running tool: %s", tool_name)
                self.status_message = f"Running {tool_name}"

                kwargs["agent"] = self
                try:
                    tool_response = self.tool_caller(tool_name, **kwargs)
                except Exception as e:
                    self.logger.debug(
                        "Unhandled tool error tool_name=%s kwargs=%s err=%r",
                        tool_name,
                        kwargs,
                        e,
                        exc_info=True,
                    )
                    raise

                self.logger.debug(f"Tool {tool_name} response : {tool_response}")
                already_called.add(tool_name)
                tool_response.tool_name = tool_name
                processed_tool_txt += "\n" + tool_txt
                processed_messages.append(tool_response)

                if isinstance(tool_response, FailedToolResult):
                    self.status_message = f"{tool_name} failed"
                    break

                self.status_message = f"Tool succeeded: {tool_name}"

                if isinstance(tool_response, AssistantResponse):
                    break

            # we append the processed messages
            self.append_message(AttemptedToolCall(processed_tool_txt))
            for x in processed_messages:
                self.append_message(x)

            last_tool = processed_messages[-1]
            if isinstance(last_tool, FailedToolResult):
                self.status_message = f"{last_tool.tool_name} failed"
                continue

            self._trim_attempted_tool_calls()

            if isinstance(last_tool, AssistantResponse):
                # this is the main response from the agent
                self.last_result_txt = last_tool.txt
                self.status_message = "IDLE"
                return last_tool

    def __call__(self, *args, **kwargs) -> str:
        """Public entry point to process a user message."""
        self.is_running = True
        try:
            try:
                return self.run(*args, **kwargs)
            except Exception:
                self.logger.exception("Unhandled exception in agent run")
                raise
        finally:
            self.is_running = False
