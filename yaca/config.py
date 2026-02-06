import os

import yaml

_CACHED_CONFIG = None
_CACHED_CONFIG_WARNINGS = []


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


def _find_project_root_default_config_path() -> str:
    cwd = os.path.abspath(os.getcwd())
    current = cwd
    while True:
        candidate = os.path.join(current, "default_config.yaml")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.join(cwd, "default_config.yaml")


def _ensure_yaca_dir_in_cwd() -> str:
    yaca_dir = os.path.join(os.getcwd(), ".yaca")
    os.makedirs(yaca_dir, exist_ok=True)
    return yaca_dir


def _ensure_user_config_exists(yaca_dir: str) -> str:
    user_config_path = os.path.join(yaca_dir, "user_config.yaml")
    if not os.path.exists(user_config_path):
        with open(user_config_path, "w") as f:
            f.write("")
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
        _CACHED_CONFIG_WARNINGS.append(
            f"Config warning: Could not parse YAML in {user_config_path}. Fix the YAML syntax (indentation/quotes) or clear the file."
        )
        return {}

    if parsed is None:
        return {}

    if not isinstance(parsed, dict):
        _CACHED_CONFIG_WARNINGS.append(
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


def loading_config() -> dict:
    default_config_path = _find_project_root_default_config_path()
    default_cfg = _loading_yaml(default_config_path)

    yaca_dir = _ensure_yaca_dir_in_cwd()
    user_config_path = _ensure_user_config_exists(yaca_dir)
    user_cfg = _load_user_config(user_config_path)

    if isinstance(default_cfg, dict) and isinstance(user_cfg, dict):
        unknown_paths = _find_unknown_config_keys(default_cfg, user_cfg)
        for path in unknown_paths:
            _CACHED_CONFIG_WARNINGS.append(
                f"Config warning: Unknown config key '{path}' in {user_config_path}."
            )

    return _merging_dicts(default_cfg, user_cfg)


def get_cfg() -> dict:
    global _CACHED_CONFIG
    if _CACHED_CONFIG is None:
        _CACHED_CONFIG = loading_config()
    return _CACHED_CONFIG


def get_config_warnings() -> list[str]:
    return list(_CACHED_CONFIG_WARNINGS)


def get_cfg_value(path: str, expected_type: type = None):
    if not isinstance(path, str) or path.strip() == "":
        raise ValueError("path must be a non-empty string")

    cfg = get_cfg()

    current = cfg
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise Exception(f"Error loading {path} in config")
        current = current[part]
    if expected_type is not None and not isinstance(current, expected_type):
        raise Exception(
            f"Error parsing config. Expected {path!r} to be of type {expected_type}, but got {type(expected_type)} instead"
        )
    return current
