from ...llm.messages import HelperMessage, StarterPrompt, UserInput
from ...tools.list_files import list_files_tool
from ...tools.read_files import read_files_limited
from ..base_agent import BaseAgent


class YacaCoder(BaseAgent):
    def __init__(self, todo_list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.reset()
        self.todo_list = todo_list
        assert len(self.todo_list) > 0

        self.set_tools(
            # "open_files",
            # "list_files",
            # "search",
            "update_todo",
            "apply_diff",
            "create_file",
            "remove_path",
            # "cannot_do",
            "done_coding",
        )

    def reset(self) -> None:
        super().reset()
        self.open_files = []
        self.last_list_files = "**"
        self.todo_list = []

    # Context management
    def build_system_message(self) -> str:
        """Build the system prompt including tool descriptions and guidelines."""
        return self.prompt_loader(
            "starter_prompt",
            TOOLS_DESCRIPTION=self.tool_caller.build_tool_description(),
            TOOL_GUIDELINES=self.prompt_loader("guidelines_code"),
        )

    def build_mode_instructions(self) -> str:
        return "First, read the current open files in the editor and assess weither items in the todo list need to be updated. If not, then either do the next item in the todo, or attempt task completion. Answer me with one or multiple independant tool calls."

    def build_todo_context(self) -> str | None:
        """Render the current TODO list for injection into the LLM context."""
        if not self.todo_list:
            return None

        assert isinstance(self.todo_list, list)
        out = "Here is the current TODO list:\n[\n"
        for dic in self.todo_list:
            out += f'"item" : {dic["item"]!r}, "status" : {dic["status"]!r}\n'
        return out + "\n]"

    def build_open_files_context(self) -> str | None:
        """Render current open files contents for injection into the LLM context."""
        if not self.open_files:
            return None

        context = "Here are the open files in my coding editor:\n"
        context += read_files_limited(self.open_files, max_files=1000)
        return context

    def prepare_conversation(self) -> list[dict]:
        """Build the LLM-ready conversation, injecting helper context messages."""

        self.conversation = super().prepare_conversation()

        # refreshing or adding starter prompt
        if len(self.conversation) == 0 or not isinstance(
            self.conversation[0], StarterPrompt
        ):
            self.append_message(StarterPrompt(self.build_system_message()), 0)
        else:
            self.conversation[0] = StarterPrompt(self.build_system_message())

        # finding the last user input
        for last_user_input_id in range(len(self.conversation) - 1, -1, -1):
            if isinstance(self.conversation[last_user_input_id], UserInput):
                break
        else:
            last_user_input_id = None

        assert last_user_input_id is not None
        assert isinstance(
            self.conversation[last_user_input_id], UserInput
        ), self.conversation[last_user_input_id]

        # adding helper messages around user input
        self.conversation = (
            self.conversation[:last_user_input_id]
            + [
                HelperMessage(self.build_open_files_context()),
                HelperMessage(self.build_todo_context()),
                self.conversation[last_user_input_id],
                HelperMessage(self.build_mode_instructions()),
            ]
            + self.conversation[last_user_input_id + 1 :]
        )

        return self.conversation
