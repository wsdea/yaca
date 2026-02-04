import json
import re


def find_json(txt) -> dict | list | None:
    """
    Finds the last instance of a JSON block in the string and converts it to a Python object.

    Args:
        txt (str): The input string that may contain a JSON block.

    Returns:
        dict or None: The Python object representation of the last JSON block, or None if no JSON block is found.
    """
    # Find all matches of the pattern in the string
    matches = re.findall(r"```json(.*?)```", txt, re.DOTALL)

    if matches:
        # Getting the last match
        last_match = matches[-1]
    else:
        # If no matches, we try to parse the whole answer
        # gpt-oss likes not to return ```json
        last_match = txt

    # remove trailing commas
    last_match = re.sub(r",(\n)*}", "}", last_match)
    last_match = re.sub(r",(\n)*]", "]", last_match)

    try:
        return json.loads(last_match.strip())
    except json.JSONDecodeError:
        return None
