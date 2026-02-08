import os
import shutil

import pytest

import yaca.config
import yaca.tools.safety


def pytest_ignore_collect(collection_path, config):
    """
    Pytest hook to ignore the ``projects_mirror`` directory during test collection.
    This prevents pytest from trying to collect any test files that might be
    generated inside the mirror folder.
    """
    # ``path`` can be a ``Path`` object or a string; convert to string for safety.
    path_str = str(collection_path)
    # If the path ends with or contains the ``projects_mirror`` directory, ignore it.
    if "projects_mirror" in path_str.split(os.sep):
        return True
    return None


@pytest.fixture(scope="session", autouse=True)
def clean_projects_mirror():
    """
    Remove the `tests/projects_mirror` directory before any tests run.
    This ensures a clean state for tests that rely on this folder.
    """
    mirror_path = os.path.join(os.path.dirname(__file__), "projects_mirror")
    if os.path.isdir(mirror_path):
        shutil.rmtree(mirror_path)


@pytest.fixture(autouse=True)
def yaca_test_cfg(monkeypatch) -> None:
    def _get_cfg():
        return {
            "safety": {
                "ignore_patterns": [],
                "unsafe_keywords": [],
                "unsafe_attr_calls": [],
            },
            "tools": {
                "list_files": {"max_depth": 25},
                "read_files": {"max_files_to_read": 50},
                "search": {"max_results": 500},
            },
        }

    monkeypatch.setattr(yaca.config, "get_cfg", _get_cfg)
    yaca.tools.safety._UNSAFE_TRIPPED = False
