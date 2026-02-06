import glob
import os
import shutil

from .app import YacaTextualApp
from .history_manager import HistoryManager
from ..agents import YacaPlanner


def cleanup_agent_debug_artifacts() -> None:
    AGENTS_LOG_FOLDER = os.path.join(os.getcwd(), ".yaca", ".state", "agent_logs")
    if os.path.exists(AGENTS_LOG_FOLDER):
        shutil.rmtree(AGENTS_LOG_FOLDER, ignore_errors=True)
        os.makedirs(exist_ok=True)



def main() -> None:
    """Launch the Textual UI."""
    cleanup_agent_debug_artifacts()
    agent = YacaPlanner()

    history_file = os.path.join(agent.STATE_FOLDER, "history.json")
    history_manager = HistoryManager(history_file)
    app = YacaTextualApp(agent, history=history_manager)
    app.run()
