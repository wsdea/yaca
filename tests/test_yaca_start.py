import os

import pytest

from yaca.agents import YacaCoder
from yaca.ui import YacaTextualApp
from yaca.ui.history_manager import HistoryManager


@pytest.fixture(autouse=True)
def _cwd_tmp_path(tmp_path):
    """Fixture to change current working directory in each tests"""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old_cwd)


@pytest.mark.fast
def test_yaca_init() -> None:
    agent = YacaCoder(_pytest=True)
    assert "ask_questions" not in agent.tool_caller.tools, agent.tool_caller.tools


@pytest.mark.fast
def test_yaca_ui_init() -> None:
    agent = YacaCoder(_pytest=True)

    history_file = os.path.join(agent.STATE_FOLDER, "history.json")
    history_manager = HistoryManager(history_file)
    app = YacaTextualApp(agent, history_manager)
