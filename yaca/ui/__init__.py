import glob
import os

from .app import YacaTextualApp
from .history_manager import HistoryManager
from ..agents import YacaPlanner


def cleanup_agent_debug_artifacts() -> None:
    STATE_FOLDER = os.path.join(os.getcwd(), ".yaca", ".state")

    debug_files = glob.glob(os.path.join(STATE_FOLDER, "**", "debug*.log"), recursive=True)
    debug_files += glob.glob(os.path.join(STATE_FOLDER,"**", "llm_log_*"), recursive=True)
    for file_path in debug_files:
        try:
            os.remove(file_path)
        except (FileNotFoundError, PermissionError):
            pass


def main() -> None:
    """Launch the Textual UI."""
    cleanup_agent_debug_artifacts()
    agent = YacaPlanner()

    history_file = os.path.join(agent.STATE_FOLDER, "history.json")
    history_manager = HistoryManager(history_file)
    app = YacaTextualApp(agent, history=history_manager)
    app.run()
