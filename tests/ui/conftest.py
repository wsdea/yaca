import os

import pytest

from tests.conftest import USER_CONFIG_YAML


@pytest.fixture(autouse=True)
def ui_test_cwd_and_user_config(tmp_path: str):
    prev_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        yaca_dir = os.path.join(tmp_path, ".yaca")
        os.makedirs(yaca_dir, exist_ok=True)

        user_config_path = os.path.join(yaca_dir, "user_config.yaml")
        with open(user_config_path, "w", encoding="utf-8") as f:
            f.write(USER_CONFIG_YAML)

        yield
    finally:
        os.chdir(prev_cwd)
