import os

import yaca.config


def _reset_config_caches() -> None:
    yaca.config._CACHED_CONFIG = None
    yaca.config._CACHED_CONFIG_WARNINGS.clear()


def test_unknown_top_level_config_key_emits_warning(tmp_path) -> None:
    _reset_config_caches()
    os.chdir(tmp_path)

    with open("default_config.yaml", "w") as f:
        f.write("known: 1\n")

    os.makedirs(".yaca", exist_ok=True)
    with open(os.path.join(".yaca", "user_config.yaml"), "w") as f:
        f.write("unknown_key: 2\n")

    yaca.config.loading_config()
    warnings = yaca.config.get_config_warnings()

    assert any("Unknown config key" in w and "unknown_key" in w for w in warnings)


def test_unknown_nested_config_key_emits_warning(tmp_path) -> None:
    _reset_config_caches()
    os.chdir(tmp_path)

    with open("default_config.yaml", "w") as f:
        f.write("llm:\n  openai:\n    max_retries: 1\n")

    os.makedirs(".yaca", exist_ok=True)
    with open(os.path.join(".yaca", "user_config.yaml"), "w") as f:
        f.write("llm:\n  unknown_nested: 1\n")

    yaca.config.loading_config()
    warnings = yaca.config.get_config_warnings()

    assert any(
        "Unknown config key" in w and "llm.unknown_nested" in w for w in warnings
    )


def test_only_known_keys_emits_no_unknown_key_warning(tmp_path) -> None:
    _reset_config_caches()
    os.chdir(tmp_path)

    with open("default_config.yaml", "w") as f:
        f.write("llm:\n  openai:\n    max_retries: 1\n")

    os.makedirs(".yaca", exist_ok=True)
    with open(os.path.join(".yaca", "user_config.yaml"), "w") as f:
        f.write("llm:\n  openai:\n    max_retries: 2\n")

    yaca.config.loading_config()
    warnings = yaca.config.get_config_warnings()

    assert not any("Unknown config key" in w for w in warnings)
