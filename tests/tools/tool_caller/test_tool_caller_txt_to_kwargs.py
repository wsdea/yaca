import pytest

# Instanciating once for the whole module
from yaca.tools.tool_caller import ToolCaller, ToolParsingError


def dummy_tool(agent):
    pass


TOOLS = {
    "read_file": dummy_tool,
    "apply_diff": dummy_tool,
    "noop": dummy_tool,
}
tc = ToolCaller(TOOLS)
tc.set_tools(list(TOOLS.keys()))


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
            '<yaca_tool name="noop" />',
            [("noop", {})],
        ),
        (
            """
            <yaca_tool name="read_file">
                <path>a.txt</path>
            </yaca_tool>

            <yaca_tool name="apply_diff">
                <diff>PATCH</diff>
            </yaca_tool>

            <yaca_tool name="noop" />
            """,
            [
                ("read_file", {"path": "a.txt"}),
                ("apply_diff", {"diff": "PATCH"}),
                ("noop", {}),
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
        "<nothing_here />",
        "",
    ],
)
def test_tool_parsing_failure(xml):
    with pytest.raises(ToolParsingError):
        tc.text_to_kwargs(xml)
