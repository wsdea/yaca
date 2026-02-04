import os

import orjson


def load_json(json_path):
    with open(json_path, "rb") as json_file:
        dic = orjson.loads(json_file.read())
    return dic


def save_json(json_path, records, make_dirs=True):
    """
    Save records to a JSON file. In case of error, it will restore the old version of the file.
    Args:
        json_path (str): The path to save the JSON file.
        records: The data to be saved as JSON.
        make_dirs (bool): Whether to create the directory if it does not exist.
    Raises:
        Exception: If there is an error during the JSON serialization process.
    """
    # Make sure output directory exists else create it
    if make_dirs:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Define the temporary file path
    tmp_path = json_path + ".tmp"

    try:
        # Dump JSON
        with open(tmp_path, "wb") as file:
            file.write(orjson.dumps(records, option=orjson.OPT_INDENT_2))
    except Exception as e:
        # Clean up the temporary file if it exists
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

    try:
        # Remove the existing JSON file if it exists
        os.remove(json_path)
    except FileNotFoundError:
        pass

    # Rename the temporary file to the final JSON file
    os.rename(tmp_path, json_path)
