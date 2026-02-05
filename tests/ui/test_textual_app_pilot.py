import os

import pytest

from yaca.agents import YacaPlanner
from yaca.ui.app import YacaTextualApp
from yaca.ui.history_manager import HistoryManager

original_wd = os.getcwd()
# we keep the original cache for faster tests
llm_cache_folder = os.path.join(original_wd, ".yaca", ".state", "llm_cache")


def test_textual_app_constructs(tmp_path) -> None:
    os.chdir(tmp_path)
    try:
        history_path = os.path.join(tmp_path, "history.json")
        agent = YacaPlanner(_pytest=True, llm_cache_folder=llm_cache_folder)
        history_manager = HistoryManager(history_path)
        app = YacaTextualApp(agent, history_manager)
        assert app is not None
    finally:
        os.chdir(original_wd)


@pytest.mark.fast
@pytest.mark.asyncio
async def test_textual_app_run_test_starts_and_widgets_mount(tmp_path) -> None:
    os.chdir(tmp_path)
    try:
        history_path = os.path.join(tmp_path, "history.json")
        agent = YacaPlanner(_pytest=True, llm_cache_folder=llm_cache_folder)
        history_manager = HistoryManager(history_path)
        app = YacaTextualApp(agent, history_manager)

        async with app.run_test() as pilot:
            await pilot.pause(0)
            assert app.is_running

    finally:
        os.chdir(original_wd)


@pytest.mark.fast
@pytest.mark.asyncio
async def test_textual_app_send_empty_message_does_not_crash(tmp_path) -> None:
    os.chdir(tmp_path)
    try:
        history_path = os.path.join(tmp_path, "history.json")
        agent = YacaPlanner(_pytest=True, llm_cache_folder=llm_cache_folder)
        history_manager = HistoryManager(history_path)
        app = YacaTextualApp(agent, history_manager)

        async with app.run_test() as pilot:
            await pilot.pause(0)
            assert app.is_running

            await pilot.click("#chat_input")
            await pilot.press("enter")
            await pilot.pause(0.1)

            assert app.is_running

    finally:
        os.chdir(original_wd)
