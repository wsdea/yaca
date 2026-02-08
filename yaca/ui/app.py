import asyncio
import os
import traceback

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Collapsible, Input, Markdown, Static

from ..agents import YacaPlanner
from ..config import get_cfg_value, get_config_warnings
from ..tools.safety import is_unsafe_tripped
from .history_manager import HistoryManager

YACA_STARTUP_MESSAGE = """```
           ╻ ╻┏━┓┏━╸┏━┓   ┏━╸┏━┓╺┳┓┏━╸┏━┓
           ┗┳┛┣━┫┃  ┣━┫   ┃  ┃ ┃ ┃┃┣╸ ┣┳┛
            ╹ ╹ ╹┗━╸╹ ╹   ┗━╸┗━┛╺┻┛┗━╸╹┗╸
              Yet another coding agent
```
"""


class YacaTextualApp(App):
    """Textual UI for interacting with a Yaca agent."""

    AUTO_FOCUS = "#chat_input"
    CSS_PATH = os.path.join(os.path.dirname(__file__), "app.tcss")
    BINDINGS = [
        ("ctrl+c", "cancel_and_reset", "Cancel"),
    ]

    status_message = reactive("")
    open_files = reactive([])
    conversation_text = reactive("")
    running_status = reactive("IDLE")
    last_error = reactive("")

    def __init__(self, agent: YacaPlanner, history: HistoryManager):
        super().__init__()
        self.agent = agent
        self._processing_lock = asyncio.Lock()
        self.history = history

        self._normal_placeholder = "What do you want to do today ?"
        self._model_missing_placeholder = (
            'Set llm.model in .yaca/user_config.yaml (llm:\n  model: "openai/gpt-5.2")'
        )
        self._working_placeholder_prefix = "Yaca working"
        self._working_placeholder_frames = ["", ".", "..", "..."]
        self._working_placeholder_frame_index = 0
        self._working_placeholder_timer = None

        # Local UI input history state (initialized from persisted history manager).
        self._input_history: list[str] = list(self.history.history)
        # Index into history; points *past* the last element when not browsing.
        self._history_index: int = len(self._input_history)

        self._last_rendered_conversation: str | None = None

    def compose(self) -> ComposeResult:
        with Container(id="top"):
            yield Static("", id="warnings_banner")

            with Horizontal(id="status_row"):
                yield Static("", id="status")

            with Collapsible(title="Open Files", id="open_files"):
                yield Static("", id="open_files_content")

            with Collapsible(title="Current Tasks", id="running_subagents"):
                yield Static("", id="running_subagents_content")

        with VerticalScroll(id="chat_scroll"):
            yield Markdown("", id="chat")

        with Container(id="bottom"):
            yield Input(
                placeholder=self._normal_placeholder,
                id="chat_input",
                valid_empty=False,
                select_on_focus=True,
                compact=True,
            )

    def render_open_files(self):
        return "  \n".join(self.agent.open_files)

    def render_running_subagents(self) -> str:
        rendered = []
        for name, agent in self.agent.running_subagents.items():
            status_message = agent.status_message
            if not status_message:
                status_message = "IDLE"

            header = f"{name} — {status_message}"

            if agent.todo_list:
                todo_lines = "\n".join(
                    [
                        f"- [{'x' if item['status'] == 'done' else ' '}] {item['item']}"
                        for item in agent.todo_list
                    ]
                )
                rendered.append(f"{header}\n\nTodo:\n{todo_lines}")
            else:
                rendered.append(header)

        return "\n\n".join(rendered)

    def _render_todo(self) -> tuple[str, int, int]:
        return ("Todo: (none)", 0, 0)

    def render_conversation(self):
        return self.agent.last_result_txt or YACA_STARTUP_MESSAGE

    def on_mount(self) -> None:
        self.refresh_from_agent()
        self.set_interval(0.15, self.refresh_from_agent)

    def refresh_from_agent(self) -> None:
        status_message = self.agent.status_message
        status = f"Status: {status_message}"
        self.query_one("#status", Static).update(status)

        warnings = []

        if is_unsafe_tripped():
            warnings.append(
                "YACA may have generated unsafe code. Please double-check before running commands (including tests). "
                "All command running abilities and hooks have been disabled. Review the generated code, and restart YACA to re-enable all features."
            )

        warnings.extend(get_config_warnings())

        warning_banner = self.query_one("#warnings_banner", Static)
        warning_banner.display = bool(warnings)
        if warning_banner.display:
            warning_banner.update(
                "Warnings:\n" + "\n".join([f"- {w}" for w in warnings])
            )

        open_files = self.query_one("#open_files", Collapsible)
        open_files.display = bool(self.agent.open_files)
        if open_files.display:
            open_files.title = f"Open Files: {len(self.agent.open_files)}"
            self.query_one("#open_files_content", Static).update(
                self.render_open_files()
            )

        running_subagents = self.query_one("#running_subagents", Collapsible)
        running_subagents.display = bool(self.agent.running_subagents)
        if running_subagents.display:
            running_subagents.title = (
                f"Current Subagents: {len(self.agent.running_subagents)}"
            )
            self.query_one("#running_subagents_content", Static).update(
                self.render_running_subagents()
            )

        self._refresh_chat_input_state()

        new_text = self.render_conversation()

        if new_text != self._last_rendered_conversation:
            self.query_one("#chat", Markdown).update(new_text)
            self._last_rendered_conversation = new_text

    def _get_working_placeholder(self) -> str:
        frame = self._working_placeholder_frames[
            self._working_placeholder_frame_index
            % len(self._working_placeholder_frames)
        ]
        return f"{self._working_placeholder_prefix}{frame}"

    def _tick_working_placeholder(self) -> None:
        if not self.agent.is_running:
            return

        chat_input = self.query_one("#chat_input", Input)
        self._working_placeholder_frame_index += 1
        chat_input.placeholder = self._get_working_placeholder()

    def _start_working_placeholder_animation(self) -> None:
        if self._working_placeholder_timer is not None:
            return

        self._working_placeholder_frame_index = 0
        chat_input = self.query_one("#chat_input", Input)
        chat_input.placeholder = self._get_working_placeholder()
        self._working_placeholder_timer = self.set_interval(
            0.2, self._tick_working_placeholder
        )

    def _stop_working_placeholder_animation(self) -> None:
        if self._working_placeholder_timer is None:
            return

        self._working_placeholder_timer.stop()
        self._working_placeholder_timer = None
        self._working_placeholder_frame_index = 0

        chat_input = self.query_one("#chat_input", Input)
        chat_input.placeholder = self._normal_placeholder

    def _refresh_chat_input_state(self) -> None:
        chat_input = self.query_one("#chat_input", Input)

        model = get_cfg_value("llm.model")
        model_missing = model is None

        should_disable = bool(self.agent.is_running) or model_missing

        if self.agent.is_running:
            self._start_working_placeholder_animation()
        else:
            self._stop_working_placeholder_animation()

        if model_missing and not self.agent.is_running:
            chat_input.placeholder = self._model_missing_placeholder
        elif not self.agent.is_running:
            chat_input.placeholder = self._normal_placeholder

        if chat_input.disabled == should_disable:
            return

        chat_input.disabled = should_disable
        if should_disable:
            self.set_focus(None)
        else:
            self.set_focus(chat_input)

    async def _process_message(self, message: str) -> None:
        try:
            await asyncio.to_thread(self.agent, message)
        except Exception:
            formatted = traceback.format_exc().strip()
            print("_process_message crashed:\n\n%s", formatted)
            raise

    async def action_cancel_and_reset(self) -> None:
        chat_input = self.query_one("#chat_input", Input)
        self.last_error = ""
        should_exit = (
            not self.agent.is_running
            and chat_input.value.strip() == ""
            and len(self.agent.conversation) == 0
        )
        if should_exit:
            self.exit()
            return

        if self.agent.is_running:
            self.agent.request_cancel()
        self.agent.reset()
        self.agent.last_result_txt = ""
        self._history_index = len(self._input_history)
        self._last_rendered_conversation = None
        chat_input.value = ""
        self.call_later(self.refresh_from_agent)

    def _on_process_task_done(self, task) -> None:
        exc = task.exception()
        if exc is None:
            return

        formatted = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ).strip()
        print("Unhandled exception in agent task:\n\n%s", formatted)

        self.agent.is_running = False
        self.last_error = f"Agent crashed\n\n{type(exc).__name__}: {exc}\n\n{formatted}"
        self.call_later(self.refresh_from_agent)

        loop = asyncio.get_running_loop()
        loop.call_exception_handler(
            {
                "message": "Unhandled exception in agent task",
                "exception": exc,
                "task": task,
            }
        )

        try:
            print(formatted)
        except Exception:
            pass

        self.set_timer(0.05, lambda: self.exit(return_code=1))

    @on(Input.Submitted, "#chat_input")
    async def action_send_message(self) -> None:
        self.last_error = ""
        input = self.query_one("#chat_input", Input)
        message = input.value
        input.value = ""

        stripped = message.strip()
        if stripped == "":
            self.call_later(self.refresh_from_agent)
            return

        if stripped == "/reset":
            self.agent.reset()
            self.agent.last_result_txt = ""
            self._history_index = len(self._input_history)
            self._last_rendered_conversation = None
            input.value = ""
            self.call_later(self.refresh_from_agent)
            return

        # Persist prompt history.
        self.history.add_user_input(message)

        # Keep local UI history in sync with persisted history.
        self._input_history.append(message)
        self._history_index = len(self._input_history)

        # self._clear_and_refocus_input()
        self.call_later(self.refresh_from_agent)
        task = asyncio.create_task(self._process_message(message))
        task.add_done_callback(self._on_process_task_done)

    def _show_history_at_index(self) -> None:
        chat_input = self.query_one("#chat_input", Input)
        if self._history_index < 0:
            self._history_index = 0
        if self._history_index > len(self._input_history):
            self._history_index = len(self._input_history)

        if self._history_index == len(self._input_history):
            chat_input.value = ""
        else:
            chat_input.value = self._input_history[self._history_index]

    async def on_key(self, event) -> None:
        # Input history navigation.
        if event.key == "up":
            if self._input_history:
                event.prevent_default()
                event.stop()
                self._history_index = max(0, self._history_index - 1)
                self._show_history_at_index()
            return

        if event.key == "down":
            if self._input_history:
                event.prevent_default()
                event.stop()
                self._history_index = min(
                    len(self._input_history), self._history_index + 1
                )
                self._show_history_at_index()
            return
