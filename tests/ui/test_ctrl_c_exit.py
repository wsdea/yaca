import os
from types import SimpleNamespace

import pytest

from yaca.ui.app import YacaTextualApp
from yaca.ui.history_manager import HistoryManager
from yaca.ui.yaca_cli import YacaCLI

original_wd = os.getcwd()


class _DummyAgent:
    def __init__(self) -> None:
        self.mode = ""
        self.status_message = ""
        self.open_files = []
        self.conversation = []
        self.is_running = False
        self.todo_list = []

    def request_cancel(self) -> None:
        pass

    def reset(self) -> None:
        self.conversation = []


@pytest.mark.fast
@pytest.mark.asyncio
async def test_textual_ctrl_c_exits_when_empty_and_reset(tmp_path) -> None:
    os.chdir(tmp_path)
    try:
        history_path = os.path.join(tmp_path, "history.json")
        agent = _DummyAgent()
        history_manager = HistoryManager(history_path)
        app = YacaTextualApp(agent, history_manager)

        async with app.run_test() as pilot:
            await pilot.pause(0)
            assert app.is_running

            chat_input = app.query_one("#chat_input")
            chat_input.disabled = False
            chat_input.value = ""

            await pilot.press("ctrl+c")
            await pilot.pause(0)

            assert not app.is_running
    finally:
        os.chdir(original_wd)


@pytest.mark.fast
@pytest.mark.asyncio
async def test_textual_ctrl_c_resets_when_conversation_not_empty(tmp_path) -> None:
    os.chdir(tmp_path)
    try:
        history_path = os.path.join(tmp_path, "history.json")
        agent = _DummyAgent()
        history_manager = HistoryManager(history_path)
        app = YacaTextualApp(agent, history_manager)

        async with app.run_test() as pilot:
            await pilot.pause(0)
            agent.conversation = [SimpleNamespace(display_txt=lambda: "hi")]
            assert app.is_running

            chat_input = app.query_one("#chat_input")
            chat_input.disabled = False
            chat_input.value = "something"

            await pilot.press("ctrl+c")
            await pilot.pause(0)

            assert app.is_running
            assert agent.conversation == []
            assert chat_input.value == ""
    finally:
        os.chdir(original_wd)


def test_cli_ctrl_c_exits_when_buffer_empty(tmp_path, monkeypatch) -> None:
    os.chdir(tmp_path)
    try:
        history_path = os.path.join(tmp_path, "history.json")
        history_manager = HistoryManager(history_path)
        agent = _DummyAgent()
        cli = YacaCLI(agent, history_manager)

        calls = {"n": 0}

        def _prompt():
            calls["n"] += 1
            raise KeyboardInterrupt()

        monkeypatch.setattr(cli.session, "prompt", _prompt)
        cli.session.default_buffer.text = ""

        cli.run()
        assert calls["n"] == 1
    finally:
        os.chdir(original_wd)


def test_cli_ctrl_c_resets_when_buffer_not_empty(tmp_path, monkeypatch) -> None:
    os.chdir(tmp_path)
    try:
        history_path = os.path.join(tmp_path, "history.json")
        history_manager = HistoryManager(history_path)

        class _Agent(_DummyAgent):
            def __init__(self) -> None:
                super().__init__()
                self.cancel_calls = 0
                self.reset_calls = 0

            def request_cancel(self) -> None:
                self.cancel_calls += 1

            def reset(self) -> None:
                self.reset_calls += 1
                super().reset()

        agent = _Agent()
        cli = YacaCLI(agent, history_manager)

        calls = {"n": 0}

        def _prompt():
            calls["n"] += 1
            if calls["n"] == 1:
                raise KeyboardInterrupt()
            raise EOFError()

        monkeypatch.setattr(cli.session, "prompt", _prompt)
        cli.session.default_buffer.text = "something"

        cli.run()
        assert agent.cancel_calls == 1
        assert agent.reset_calls == 1
        assert calls["n"] == 2
    finally:
        os.chdir(original_wd)
