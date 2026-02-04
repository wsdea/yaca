import pytest

# Instanciating once for the whole module
from yaca.tools.tool_caller import ToolCaller


def dummy_tool(agent):
    pass


TOOLS = {
    "read_file": dummy_tool,
    "apply_diff": dummy_tool,
    "update_todo": dummy_tool,
}
tc = ToolCaller(TOOLS)
tc.set_tools(TOOLS)


@pytest.mark.parametrize(
    "xml, expected",
    [
        (
            """
            <yaca_tool name="read_file">
                <path>README.md</path>
            </yaca_tool>
            """,
            [("read_file", {"path": "README.md"})],
        ),
        (
            '<yaca_tool name="update_todo" />',
            [("update_todo", {})],
        ),
        (
            """
            <yaca_tool name="read_file">
                <path>a.txt</path>
            </yaca_tool>

            <yaca_tool name="apply_diff">
                <diff>PATCH</diff>
            </yaca_tool>

            <yaca_tool name="update_todo" />
            """,
            [
                ("read_file", {"path": "a.txt"}),
                ("apply_diff", {"diff": "PATCH"}),
                ("update_todo", {}),
            ],
        ),
        (
            """
            <yaca_tool name="apply_diff">
                <path>file.txt</path>
                <diff>DATA</diff>
            </yaca_tool>
            """,
            [
                (
                    "apply_diff",
                    {
                        "path": "file.txt",
                        "diff": "DATA",
                    },
                )
            ],
        ),
        (
            """
            <yaca_tool   name="read_file"   >
                  <path>
                    test.txt
                  </path>
            </yaca_tool>
            """,
            [("read_file", {"path": "test.txt"})],
        ),
    ],
)
def test_tool_parsing_success(xml, expected):
    result = tc.text_to_kwargs(xml)
    result = [x[:2] for x in result]
    assert result == expected


@pytest.mark.parametrize(
    "xml",
    [
        '<yaca_tool name="evil_tool" />',
        "<nothing_here />",
        "",
    ],
)
def test_tool_parsing_failure(xml):
    with pytest.raises(Exception):
        tc.text_to_kwargs(xml)
