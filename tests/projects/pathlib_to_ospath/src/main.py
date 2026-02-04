from pathlib import Path


def get_base_dir() -> str:
    """Return the current directory"""
    return str(Path(__file__).parent)


def list_py_files(dir_path: str) -> list[str]:
    """Return a list of .py files in the given directory."""
    return [str(p) for p in Path(dir_path).glob("*.py")]


def get_file_name(path: str) -> str:
    """Return the base name of the given path."""
    return Path(path).name


def get_parent_dir(path: str) -> str:
    """Return the parent directory of the given path."""
    return str(Path(path).parent)


def join_path(*parts: str) -> str:
    """Join multiple path components."""
    return str(Path(*parts))


def exists(path: str) -> bool:
    """Check if the path exists."""
    return Path(path).exists()


def is_file(path: str) -> bool:
    """Check if the path is a file."""
    return Path(path).is_file()


def is_dir(path: str) -> bool:
    """Check if the path is a directory."""
    return Path(path).is_dir()


def demo() -> None:
    """Demonstrate various path operations."""
    base_dir = get_base_dir()
    print("Base dir", base_dir)
    print("Joined path:", join_path(base_dir, "example", "test.txt"))
    print("Exists:", exists(base_dir))
    print("Is directory:", is_dir(base_dir))
    print("List .py files:", list_py_files(base_dir))
    sample_path = join_path(base_dir, "sample.py")
    print("File name:", get_file_name(sample_path))
    print("Parent directory:", get_parent_dir(sample_path))


if __name__ == "__main__":
    demo()
