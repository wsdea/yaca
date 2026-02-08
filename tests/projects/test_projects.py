import importlib.util
import os
import shutil

import pytest

from yaca.agents import YacaPlanner

PROJECTS_DIR = os.path.join(os.path.dirname(__file__))
PROJECTS_MIRROR_DIR = os.path.join(os.path.dirname(__file__), "..", "projects_mirror")

FAST_PROJECTS = [
    "create_file",
    "delete_file",
    "pathlib_to_ospath",
    "hello_world_human",
]

USER_CONFIG_YAML = """llm:
  model: "openai/gpt-5.2"
  api_key_env: "OPENAI_API_KEY"
"""


def discover_projects() -> list[str]:
    """
    Find project directories that contain a ``src`` folder.
    """
    projects = os.listdir(PROJECTS_DIR)
    return [x for x in projects if ".py" not in x and "__pycache__" not in x]


def run_task(working_dir, task):
    original_wd = os.getcwd()
    # we keep the original cache for faster tests
    llm_cache_file = os.path.join(original_wd, ".yaca", ".state", "llm_cache.json")
    try:
        os.chdir(working_dir)
        CHATBOT = YacaPlanner(_pytest=True, llm_cache_file=llm_cache_file)
        CHATBOT(task)
    finally:
        os.chdir(original_wd)

    return CHATBOT


def run_verification(agent, project_dir: str, mirror_src: str):
    """Execute the project's verification logic.

    Loads the ``verifications.py`` module adjacent to the original ``src``
    directory and calls its ``verify`` function, passing the path to the copied
    ``src`` folder. Returns the result of the verification.
    """
    original_wd = os.getcwd()
    assert os.path.exists(mirror_src), mirror_src
    os.chdir(mirror_src)

    verification_file = os.path.abspath(os.path.join(project_dir, "verifications.py"))
    assert os.path.exists(verification_file), verification_file

    spec = importlib.util.spec_from_file_location("verifications", verification_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        module.verify(agent, mirror_src)
    finally:
        os.chdir(original_wd)


@pytest.mark.parametrize(
    "project_name",
    [
        pytest.param(name, marks=[pytest.mark.fast])
        if name in FAST_PROJECTS
        else pytest.param(name)
        for name in discover_projects()
    ],
)
def test_project(project_name: str) -> None:
    """
    This copies src folder into the mirror dir
    Then runs the task as describe in task.py
    Then run the verifications.main function to check the task was done properly
    """
    # setting up env
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    src_dir = os.path.join(project_dir, "src")
    assert os.path.exists(src_dir), src_dir
    mirror = os.path.join(PROJECTS_MIRROR_DIR, project_name)
    shutil.rmtree(mirror, ignore_errors=True)
    src_mirror = os.path.join(mirror, "src")
    shutil.copytree(src_dir, src_mirror)

    yaca_dir = os.path.join(src_mirror, ".yaca")
    os.makedirs(yaca_dir, exist_ok=True)
    with open(os.path.join(yaca_dir, "user_config.yaml"), "w", encoding="utf-8") as f:
        f.write(USER_CONFIG_YAML)

    # running task
    with open(os.path.join(project_dir, "task.txt")) as f:
        task = f.read()

    agent = run_task(src_mirror, task)

    # verifying task
    run_verification(agent, project_dir, src_mirror)
