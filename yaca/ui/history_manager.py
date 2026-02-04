import json
import os


class HistoryManager:
    """Persistent store of user input history for YACA CLI/UI."""

    def __init__(self, path) -> None:
        self.path = path
        self._history = self._load()

    @property
    def history(self) -> list[str]:
        return list(self._history)

    def add_user_input(self, message: str) -> None:
        message = message.strip()
        if not message:
            return
        self._history.append(message)
        self._save()

    def _load(self) -> list[str]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                return list(data)
            if isinstance(data, list) and all(isinstance(x, dict) for x in data):
                migrated: list[str] = []
                for x in data:
                    if isinstance(x, dict):
                        msg = x.get("message")
                        if isinstance(msg, str) and msg.strip():
                            migrated.append(msg.strip())
                return migrated
        except Exception:
            return []
        return []

    def _save(self) -> None:
        folder = os.path.dirname(self.path) or "."
        os.makedirs(folder, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._history, f, ensure_ascii=False, indent=2)
