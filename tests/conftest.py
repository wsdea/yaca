import os
import shutil

import pytest


def pytest_ignore_collect(path, config):
    """
    Pytest hook to ignore the ``projects_mirror`` directory during test collection.
    This prevents pytest from trying to collect any test files that might be
    generated inside the mirror folder.
    """
    # ``path`` can be a ``Path`` object or a string; convert to string for safety.
    path_str = str(path)
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
