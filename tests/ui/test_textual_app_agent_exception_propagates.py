import asyncio
import os

import pytest

from yaca.ui.app import YacaTextualApp
from yaca.ui.history_manager import HistoryManager


class _FailingAgent:
    def __init__(self) -> None:
        self.open_files = []
        self.running_subagents = {}
        self.todo_list = []
        self.conversation = []
        self.status_message = ""
        self.is_running = False
        self.last_result_txt = ""

    def request_cancel(self) -> None:
        return

    def reset(self) -> None:
        return

    def __call__(self, message: str) -> None:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_textual_app_agent_exception_propagates(tmp_path) -> None:
    agent = _FailingAgent()
    history_path = os.path.join(tmp_path, "history.json")
    history = HistoryManager(history_path)
    app = YacaTextualApp(agent, history)

    async with app.run_test() as pilot:
        chat_input = app.query_one("#chat_input")
        chat_input.value = "hello"
        await pilot.press("enter")

        await asyncio.sleep(0.2)

        assert app.last_error
        assert "Agent crashed" in app.last_error
        assert "RuntimeError" in app.last_error
        assert "boom" in app.last_error

        await pilot.pause(0.2)
        assert not app.is_running
