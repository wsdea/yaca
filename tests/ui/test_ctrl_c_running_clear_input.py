import os

import pytest

from yaca.ui.app import YacaTextualApp
from yaca.ui.history_manager import HistoryManager


class _DummyAgent:
    def __init__(self) -> None:
        self.mode = ""
        self.status_message = ""
        self.open_files = []
        self.running_subagents = {}
        self.conversation = []
        self.todo_list = []
        self.is_running = True
        self.last_result_txt = ""
        self.cancel_calls = 0
        self.reset_calls = 0

    def request_cancel(self) -> None:
        self.cancel_calls += 1

    def reset(self) -> None:
        self.reset_calls += 1
        self.conversation = []


@pytest.mark.fast
@pytest.mark.asyncio
async def test_textual_ctrl_c_when_running_resets_and_clears_input(tmp_path) -> None:
    history_path = os.path.join(tmp_path, "history.json")
    agent = _DummyAgent()
    history_manager = HistoryManager(history_path)
    app = YacaTextualApp(agent, history_manager)

    async with app.run_test() as pilot:
        await pilot.pause(0)

        chat_input = app.query_one("#chat_input")
        chat_input.disabled = False
        chat_input.value = "something"

        await pilot.press("ctrl+c")
        await pilot.pause(0)

        assert app.is_running
        assert agent.cancel_calls == 1
        assert agent.reset_calls == 1
        assert chat_input.value == ""
