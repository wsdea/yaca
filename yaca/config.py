import os

import yaml

_CACHED_CONFIG_WARNINGS = []
_CONFIG_WARNINGS_SET = set()


def _loading_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _merging_dicts(base, override):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merging_dicts(base[key], value)
        else:
            base[key] = value
    return base


def _load_default_config() -> dict:
    p = os.path.join(os.path.dirname(__file__), "default_config.yaml")
    assert os.path.exists(p)
    return _loading_yaml(str(p))


def _ensure_yaca_dir_in_cwd() -> str:
    yaca_dir = os.path.join(os.getcwd(), ".yaca")
    os.makedirs(yaca_dir, exist_ok=True)
    return yaca_dir


def _ensure_user_config_exists(yaca_dir: str) -> str:
    user_config_path = os.path.join(yaca_dir, "user_config.yaml")
    if not os.path.exists(user_config_path):
        template = """# YACA user config
# Copy/paste and edit values you want to override from default_config.yaml.
# Lines starting with '#' are comments.

llm:
  model: null
  api_key_env: "OPENAI_API_KEY"
"""
        with open(user_config_path, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"Please set-up your config in {user_config_path} and restart yaca")
        exit(0)
    return user_config_path


def _load_user_config(user_config_path: str) -> dict:
    if not os.path.exists(user_config_path):
        return {}

    with open(user_config_path, "r") as f:
        raw = f.read()

    if raw.strip() == "":
        return {}

    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError:
        _add_config_warning(
            f"Config warning: Could not parse YAML in {user_config_path}. Fix the YAML syntax (indentation/quotes) or clear the file."
        )
        return {}

    if parsed is None:
        return {}

    if not isinstance(parsed, dict):
        _add_config_warning(
            f"Config warning: YAML root in {user_config_path} must be a mapping (key/value pairs). Wrap values under keys or clear the file."
        )
        return {}

    return parsed


def _find_unknown_config_keys(
    default_cfg: dict, user_cfg: dict, prefix: str = ""
) -> list[str]:
    unknown = []
    for key, user_value in user_cfg.items():
        path = f"{prefix}.{key}" if prefix else str(key)

        if key not in default_cfg:
            unknown.append(path)
            continue

        default_value = default_cfg[key]
        if isinstance(default_value, dict) and isinstance(user_value, dict):
            unknown.extend(_find_unknown_config_keys(default_value, user_value, path))

    return unknown


def _add_config_warning(message: str) -> None:
    if message in _CONFIG_WARNINGS_SET:
        return
    _CONFIG_WARNINGS_SET.add(message)
    _CACHED_CONFIG_WARNINGS.append(message)


def load_cfg() -> dict:
    default_cfg = _load_default_config()

    yaca_dir = _ensure_yaca_dir_in_cwd()
    user_config_path = _ensure_user_config_exists(yaca_dir)
    user_cfg = _load_user_config(user_config_path)

    if isinstance(default_cfg, dict) and isinstance(user_cfg, dict):
        unknown_paths = _find_unknown_config_keys(default_cfg, user_cfg)
        for path in unknown_paths:
            _add_config_warning(
                f"Config warning: Unknown config key '{path}' in {user_config_path}."
            )

    merged = _merging_dicts(default_cfg, user_cfg)

    llm = merged["llm"]
    model = llm["model"]
    if model is None:
        _add_config_warning(
            'Config warning: llm.model is not set. Set it in .yaca/user_config.yaml, for example:\n\nllm:\n  model: "openai/gpt-5.2"\n'
        )
    elif not isinstance(model, str):
        _add_config_warning(
            f"Config warning: llm.model must be a string or null, but got {type(model)}."
        )

    return merged


def get_config_warnings() -> list[str]:
    return list(_CACHED_CONFIG_WARNINGS)


def get_cfg_value(path: str, expected_type: type = None):
    if not isinstance(path, str) or path.strip() == "":
        raise ValueError("path must be a non-empty string")

    cfg = load_cfg()

    current = cfg
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise Exception(f"Error loading {path} in config. Cfg :\n{cfg}")
        current = current[part]
    if expected_type is not None and not isinstance(current, expected_type):
        raise Exception(
            f"Error parsing config. Expected {path!r} to be of type {expected_type}, but got {type(current)} instead. Cfg :\n{cfg}"
        )
    return current
