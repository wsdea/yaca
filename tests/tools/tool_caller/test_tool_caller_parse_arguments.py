import pytest

from yaca.tools.tool_caller import ToolCaller, ToolParsingError


def dummy_func(a: int, b: bool, c: list[str], d: str = "default"):
    """Dummy function used only for signature inspection."""
    return a, b, c, d


def test_parse_arguments_success():
    caller = ToolCaller()
    raw_kwargs = {"a": "42", "b": "true", "c": '["x", "y", "z"]', "d": "provided"}
    parsed = caller.parse_arguments(dummy_func, **raw_kwargs)
    assert parsed["a"] == 42
    assert parsed["b"] is True
    assert parsed["c"] == ["x", "y", "z"]
    assert parsed["d"] == "provided"


def test_parse_arguments_defaults_and_missing():
    caller = ToolCaller()
    raw_kwargs = {"a": "7", "b": "false", "c": ""}
    # d has a default, should be omitted from parsed kwargs
    parsed = caller.parse_arguments(dummy_func, **raw_kwargs)
    assert parsed["a"] == 7
    assert parsed["b"] is False
    assert parsed["c"] == []
    assert "d" not in parsed


def test_parse_arguments_missing_required():
    caller = ToolCaller()
    raw_kwargs = {
        "a": "1",
        "b": "true",
        # c is missing and has no default
    }
    with pytest.raises(ToolParsingError) as exc:
        caller.parse_arguments(dummy_func, **raw_kwargs)
    assert "Missing required argument: c" in str(exc.value)


def test_parse_arguments_invalid_int():
    caller = ToolCaller()
    raw_kwargs = {"a": "not-an-int", "b": "true", "c": "item"}
    with pytest.raises(ToolParsingError) as exc:
        caller.parse_arguments(dummy_func, **raw_kwargs)
    assert "Cannot parse int for argument a" in str(exc.value)


def test_parse_arguments_invalid_bool():
    caller = ToolCaller()
    raw_kwargs = {"a": "10", "b": "maybe", "c": "item"}
    with pytest.raises(ToolParsingError) as exc:
        caller.parse_arguments(dummy_func, **raw_kwargs)
    assert "Cannot parse bool for argument b" in str(exc.value)
