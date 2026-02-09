import pytest

from yaca.tools.tool_caller import ToolCaller, ToolParsingError


def dummy_tool(agent: str):
    return agent


def dummy_func(a: int, b: bool, c: list[str], d: str = "default"):
    """Dummy function used only for signature inspection."""
    return a, b, c, d


def test_parse_arguments_success():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {
        "agent": "agent",
        "a": "42",
        "b": "true",
        "c": '["x", "y", "z"]',
        "d": "provided",
    }
    parsed = caller.parse_arguments(dummy_func, **raw_kwargs)
    assert parsed["a"] == 42
    assert parsed["b"] is True
    assert parsed["c"] == ["x", "y", "z"]
    assert parsed["d"] == "provided"


def test_parse_arguments_defaults_and_missing():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {"agent": "agent", "a": "7", "b": "false", "c": ""}
    # d has a default, should be omitted from parsed kwargs
    parsed = caller.parse_arguments(dummy_func, **raw_kwargs)
    assert parsed["a"] == 7
    assert parsed["b"] is False
    assert parsed["c"] == [""]
    assert "d" not in parsed


def test_parse_arguments_missing_required():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {
        "agent": "agent",
        "a": "1",
        "b": "true",
        # c is missing and has no default
    }
    with pytest.raises(ToolParsingError) as exc:
        caller.parse_arguments(dummy_func, **raw_kwargs)
    assert "Missing required argument(s): c" in str(exc.value)


def test_parse_arguments_invalid_int():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {"agent": "agent", "a": "not-an-int", "b": "true", "c": "item"}
    with pytest.raises(ToolParsingError) as exc:
        caller.parse_arguments(dummy_func, **raw_kwargs)
    assert "Cannot parse int for argument a" in str(exc.value)


def test_parse_arguments_invalid_bool():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {"agent": "agent", "a": "10", "b": "maybe", "c": "item"}
    with pytest.raises(ToolParsingError) as exc:
        caller.parse_arguments(dummy_func, **raw_kwargs)
    assert "Cannot parse bool for argument b" in str(exc.value)


def test_parse_arguments_list_from_item_tags():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {
        "agent": "agent",
        "a": "42",
        "b": "true",
        "c": """
            <item> x </item>
            <item>
                y
            </item>
            <item>z</item>
        """,
    }
    parsed = caller.parse_arguments(dummy_func, **raw_kwargs)
    assert parsed["c"] == ["x", "y", "z"]


def test_parse_arguments_list_from_repeated_non_item_tags():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {
        "agent": "agent",
        "a": "42",
        "b": "true",
        "c": """
            <foo> x </foo>
            <foo>
                y
            </foo>
            <foo>z</foo>
        """,
    }
    parsed = caller.parse_arguments(dummy_func, **raw_kwargs)
    assert parsed["c"] == ["x", "y", "z"]


def test_parse_arguments_list_single_xml_tag_is_not_list():
    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {"agent": "agent", "a": "42", "b": "true", "c": "<foo>bar</foo>"}
    parsed = caller.parse_arguments(dummy_func, **raw_kwargs)
    assert parsed["c"] == ["bar"]


def test_parse_arguments_list_item_tags_does_not_affect_str():
    def func_with_str(agent: str, s: str):
        return agent, s

    caller = ToolCaller(all_tools={"dummy": dummy_tool}, hook_caller=None)
    raw_kwargs = {"agent": "agent", "s": "<item>a</item><item>b</item>"}
    parsed = caller.parse_arguments(func_with_str, **raw_kwargs)
    assert parsed["s"] == "<item>a</item><item>b</item>"
