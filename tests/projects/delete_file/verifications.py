import os


def verify(agent, src_folder: str):
    """
    Verify that `sample.txt` has been deleted from the src folder.
    """
    sample_path = os.path.join(src_folder, "sample.txt")
    assert not os.path.exists(sample_path), (
        f"`sample.txt` still exists at {sample_path}"
    )

    assert "sample.txt" in os.listdir(agent.RECYCLE_BIN), os.listdir(agent.RECYCLE_BIN)
