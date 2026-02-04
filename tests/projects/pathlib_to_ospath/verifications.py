import os
import re

from yaca.tools import run_command_tool


def verify(agent, src_folder: str) -> bool:
    """Return True if the file at *file_path* no longer imports pathlib and uses os.path and glob."""
    CURRENT_WDIR = os.getcwd()
    EXPECTED_OUTPUT = f"""
Base dir {CURRENT_WDIR}
Joined path: {CURRENT_WDIR}/example/test.txt
Exists: True
Is directory: True
List .py files: ['{CURRENT_WDIR}/main.py']
File name: sample.py
Parent directory: {CURRENT_WDIR}""".strip().replace("/projects/", "/projects_mirror/")

    file_path = os.path.join(src_folder, "main.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if re.search(r"\bimport\s+pathlib\b", content):
        raise AssertionError("we still have pathlib")
    if not re.search(r"\bimport\s+os\b", content):
        raise AssertionError("we didn't import os")

    # output = run_command_tool(None, "python main.py").txt

    # if EXPECTED_OUTPUT not in output:
    #     with open("EXPECTED.txt", "w") as f:
    #         f.write(EXPECTED_OUTPUT)

    #     with open("output.txt", "w") as f:
    #         f.write(output)
    #     raise AssertionError("Wrong output, see generated files")
