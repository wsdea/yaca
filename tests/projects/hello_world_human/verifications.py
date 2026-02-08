import glob
import os

from yaca.tools.read_files import read_file


def verify(agent, src_folder: str) -> None:
    required = ["helloworld.py", "hellohuman.py"]

    for filename in required:
        matches = glob.glob(os.path.join(src_folder, filename))
        if len(matches) != 1:
            raise AssertionError(
                f"Expected exactly one file named {filename} in {src_folder}"
            )

        content = read_file(matches[0])

        if 'if __name__ == "__main__":' not in content:
            raise AssertionError(f"{filename} must contain a __main__ guard")

        if "print(" not in content:
            raise AssertionError(f"{filename} must contain a print(...) call")
