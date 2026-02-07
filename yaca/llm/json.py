import os
import time

import orjson


def load_json(json_path):
    with open(json_path, "rb") as json_file:
        dic = orjson.loads(json_file.read())
    return dic


def _lock_path_for(path: str) -> str:
    return path + ".lock"


def _acquire_lock(lock_path: str, timeout_seconds: int = 10, retry_sleep_seconds: float = 0.05):
    start = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if (time.time() - start) >= timeout_seconds:
                raise TimeoutError(f"Could not acquire lock: {lock_path}")
            time.sleep(retry_sleep_seconds)


def _release_lock(lock_path: str):
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass


def save_json(
    json_path: str,
    records,
    make_dirs: bool = True,
    use_lock: bool = False,
    lock_timeout_seconds: int = 10,
    retry_sleep_seconds: float = 0.05,
):
    """
    Save records to a JSON file. In case of error, it will restore the old version of the file.
    Args:
        json_path (str): The path to save the JSON file.
        records: The data to be saved as JSON.
        make_dirs (bool): Whether to create the directory if it does not exist.
    Raises:
        Exception: If there is an error during the JSON serialization process.
    """
    if make_dirs:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

    lock_path = _lock_path_for(json_path)
    if use_lock:
        _acquire_lock(
            lock_path,
            timeout_seconds=lock_timeout_seconds,
            retry_sleep_seconds=retry_sleep_seconds,
        )

    tmp_path = json_path + f".{os.getpid()}.tmp"

    try:
        try:
            with open(tmp_path, "wb") as file:
                file.write(orjson.dumps(records, option=orjson.OPT_INDENT_2))
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise e

        os.replace(tmp_path, json_path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        if use_lock:
            _release_lock(lock_path)
