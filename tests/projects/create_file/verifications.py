import os

from yaca.tools.read_files import read_file


def verify(agent, src_folder: str):
    files = os.listdir(src_folder)
    files = [x for x in files if not x.startswith(".")]
    assert sorted(files) == sorted(["hello.py", "hi.txt"]), files

    txt = read_file(os.path.join(src_folder, "hello.py"))
    # checks that when running it, it prints hello world
    assert "hello world" in txt, txt
    assert "print(" in txt, txt
    assert len([line for line in txt.splitlines() if line.strip()]) < 5, txt
