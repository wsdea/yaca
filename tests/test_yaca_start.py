import os

import pytest

from yaca.agents import YacaPlanner
from yaca.ui import YacaTextualApp
from yaca.ui.history_manager import HistoryManager

from .conftest import USER_CONFIG_YAML


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
def test_yaca_ui_init() -> None:
    config_dir = os.path.join(os.getcwd(), ".yaca")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "user_config.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(USER_CONFIG_YAML)

    agent = YacaPlanner(_pytest=True)

    history_file = os.path.join(agent.STATE_FOLDER, "history.json")
    history_manager = HistoryManager(history_file)
    app = YacaTextualApp(agent, history_manager)
