import os

from .app import YacaTextualApp
from .history_manager import HistoryManager
from ..agents import YacaPlanner


def main() -> None:
    """Launch the Textual UI."""
    agent = YacaPlanner()
    history_file = os.path.join(agent.STATE_FOLDER, "history.json")
    history_manager = HistoryManager(history_file)
    app = YacaTextualApp(agent, history=history_manager)
    app.run()
