from ...llm.messages import HelperMessage, StarterPrompt, UserInput
from ...tools.list_files import list_files_tool
from ...tools.read_files import read_files_limited
from ..base_agent import BaseAgent


class YacaPlanner(BaseAgent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.open_files = []
        self.last_list_files = "**"

        self.set_tools(
            "open_files",
            "list_files",
            "search",
            "ask_questions",
            "start_coding_task",
        )

    # Context management
    def build_system_message(self) -> str:
        """Build the system prompt including tool descriptions and guidelines."""
        return self.prompt_loader(
            "starter_prompt",
            TOOLS_DESCRIPTION=self.tool_caller.build_tool_description(),
            TOOL_GUIDELINES=self.prompt_loader("guidelines_plan"),
        )

    def build_mode_instructions(self) -> str:
        return "Think about the best tool to call at this time and I will give you the result. If asked about a coding task, your final tool will be a creating the todo for that task. Answer me with one or multiple independant tool calls."

    def build_project_structure(self) -> str:
        """Return a human-readable project tree snippet for LLM context."""
        structure = list_files_tool(
            self, self.last_list_files, return_message=False
        ).txt

        return f"Here is a glimpse of my codebase:\n{structure}"

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
                HelperMessage(self.build_project_structure()),
                HelperMessage(self.build_open_files_context()),
                self.conversation[last_user_input_id],
                HelperMessage(self.build_mode_instructions()),
            ]
            + self.conversation[last_user_input_id + 1 :]
        )

        return self.conversation
