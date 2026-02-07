import html
import inspect
import json
import re

from ..llm import FailedToolResult, SuccessToolResult


class ToolParsingError(Exception):
    pass


class ToolCaller:
    """Calls tools with argument validation and uniform result handling.

    Args:
        tools (list[str] | None): Optional list of tool names to expose. If None, all available tools are exposed.
    """

    def __init__(self, all_tools: dict, hook_caller=None):
        self.ALL_TOOLS = all_tools
        self.hook_caller = hook_caller

        for name, fun in self.ALL_TOOLS.items():
            sig = inspect.signature(fun)
            assert (
                "agent" in sig.parameters
            ), f"`agent` parameter is missing for {name} : {sig.parameters}"

    def add_tool(self, name, fun):
        self.ALL_TOOLS[name] = fun

    def set_tools(self, tool_names):
        self.tools = {name: self.ALL_TOOLS[name] for name in tool_names}

    def build_tool_description(self) -> str:
        """Build a description of available tools for the Jinja template."""
        assert hasattr(self, "tools"), "You need to call set_tools first"
        descriptions = []
        for name, func in self.tools.items():
            doc = func.__doc__
            if not doc:
                raise Exception(f"{name} has no docstring")

            descriptions.append(f"- {name}:\n    {doc.strip()}\n\n")
        return "\n".join(descriptions).strip()

    def clean_xml(self, xml_text: str):
        """Trying to parse when xml is not perfect"""
        xml_text = xml_text.strip().replace("\\\\", "\\")
        xml_text = html.unescape(xml_text)
        if not xml_text.endswith("</yaca_tool>"):
            xml_text += "</yaca_tool>"

        xml_text = xml_text.replace("<![CDATA[", "")
        xml_text = xml_text.replace("]]>", "")

        return xml_text

    def normalize_for_fingerprint(self, x):
        """Function to normalized the kwargs for hash computation"""
        if isinstance(x, dict):
            out = {}
            for k in sorted(x.keys()):
                if k == "agent":
                    continue
                out[str(k)] = self.normalize_for_fingerprint(x[k])
            return out

        if isinstance(x, list):
            return [self.normalize_for_fingerprint(v) for v in x]

        if isinstance(x, tuple):
            return [self.normalize_for_fingerprint(v) for v in x]

        return x

    def kwargs_fingerprint(self, kwargs: dict) -> str:
        """Computes the hash of the kwargs"""
        normalized = self.normalize_for_fingerprint(kwargs)
        return json.dumps(
            normalized, sort_keys=True, separators=(",", ":"), default=str
        )

    def text_to_kwargs(self, xml_text: str) -> list[tuple]:
        assert hasattr(self, "tools"), "You need to call set_tools first"

        """Parsing yaca_tool XML blocks and returning ordered list of (tool_name, kwargs)."""

        xml_text = self.clean_xml(xml_text)

        tool_calls = []
        seen = set()

        tool_pattern = re.compile(
            r"""
            <\s*yaca_tool\b
                [^>]*name\s*=\s*"([^"]+)"[^>]*           # extracting tool name
                (?:                                     # branching between:
                    />                                  # self-closing form
                |                                     # OR
                    >\s*(.*?)\s*</\s*yaca_tool\s*>      # normal block with body
                )
            """,
            re.DOTALL | re.VERBOSE,
        )

        for match in tool_pattern.finditer(xml_text):
            tool_string = match.group(0).strip()
            tool_name = match.group(1)
            inner_xml = match.group(2)

            # TODO : when error, only return a small xml_text where the error occurs
            if tool_name not in self.tools:
                raise ToolParsingError(
                    f"Unknown tool {tool_name}, available tools are {list(self.tools)}"
                )

            kwargs = {}

            if inner_xml:
                for arg_match in re.finditer(
                    r"<\s*([A-Za-z_][\w-]*)\b[^>]*>(.*?)</\s*\1\s*>",
                    inner_xml,
                    re.DOTALL,
                ):
                    arg_name = arg_match.group(1)
                    arg_value = arg_match.group(2).strip()

                    kwargs[arg_name] = arg_value

            call_key = (tool_name, self.kwargs_fingerprint(kwargs))
            if call_key in seen:
                # we dont run twice the same tool with the same kwargs
                continue
            seen.add(call_key)

            tool_calls.append((tool_name, kwargs, tool_string))

        if not tool_calls:
            raise ToolParsingError("No yaca_tool calls found or malformed XML.")

        return tool_calls

    def parse_arguments(self, fun, **kwargs):
        """
        All kwargs are strings, this function converts them to
        str, int, list[str] or bool depending on fun signature
        returns an error if type is missing for an arg
        """
        sig = inspect.signature(fun)
        assert "agent" in kwargs, "Agent kwarg is not provided"
        new_kwargs = {}
        for name, param in sig.parameters.items():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            if name not in kwargs:
                if param.default is not inspect._empty:
                    continue
                raise ToolParsingError(f"Missing required argument: {name}")

            raw = kwargs[name]
            ann = param.annotation

            # agent is a special argument, we always include it
            if name == "agent":
                new_kwargs[name] = raw
                continue

            if ann is inspect._empty:
                raise Exception(
                    f"Function {fun} is missing a type annotation for {param!r}"
                )

            if ann is str:
                new_kwargs[name] = raw
                continue

            if ann is bool:
                lowered = str(raw).lower()
                if lowered in ("true", "1", "yes"):
                    new_kwargs[name] = True
                elif lowered in ("false", "0", "no"):
                    new_kwargs[name] = False
                else:
                    raise ToolParsingError(
                        f"Cannot parse bool for argument {name}: {raw}"
                    )
                continue

            if ann is int:
                try:
                    new_kwargs[name] = int(raw)
                except ValueError:
                    raise ToolParsingError(
                        f"Cannot parse int for argument {name}: {raw}"
                    )
                continue

            origin = getattr(ann, "__origin__", None)
            if origin is list or ann is list:
                if raw == "":
                    new_kwargs[name] = []
                    continue

                stripped = str(raw).strip()

                if stripped.startswith("<"):
                    tags = re.findall(
                        r"<\s*([A-Za-z_][\w-]*)\b[^>]*>(.*?)</\s*\1\s*>",
                        stripped,
                        flags=re.DOTALL,
                    )
                    if len(tags) >= 1:
                        first_tag = tags[0][0]
                        if all(t[0] == first_tag for t in tags):
                            new_kwargs[name] = [
                                html.unescape(x[1]).strip() for x in tags
                            ]
                            continue

                # first trying to parse python strings
                try:
                    new_kwargs[name] = json.loads(raw)
                    assert isinstance(new_kwargs[name], list)
                    for x in new_kwargs[name]:
                        assert isinstance(x, str)
                    continue
                except (json.JSONDecodeError, AssertionError):
                    pass

                # fallback to one item per line
                lines = raw.splitlines()
                new_kwargs[name] = [x.lstrip("- ").strip() for x in lines if x.strip()]

                continue

                # raise ToolParsingError(
                #     f'Cannot parse list of strings for argument {name} : {raw}. Use python syntax'
                # )

            raise Exception(f"Unhandled type annotation {name=}, {param=}")

        return new_kwargs

    def __call__(self, tool_name, **kwargs):
        """Validate arguments and invoke the requested tool.

        Args:
            tool_name (str): Name of the tool to call.
            n_attempts (str) : Current number of attempts for that tool
            *args: Positional arguments to pass to the tool.
            **kwargs: Keyword arguments to pass to the tool.

        Returns:
            SuccessToolResult | FailedToolResult: the tool result.
        """
        assert hasattr(self, "tools"), "You need to call set_tools first"

        if tool_name not in self.tools:
            return FailedToolResult(f"Tool '{tool_name}' is not available.")

        tool = self.tools[tool_name]

        # validating function arguments
        try:
            sig = inspect.signature(tool)
            sig.bind(**kwargs)
        except TypeError as e:
            return FailedToolResult(f"Argument validation error: {e}")

        # convert string arguments to proper types based on tool signature
        try:
            parsed_kwargs = self.parse_arguments(tool, **kwargs)
        except ToolParsingError as e:
            return FailedToolResult(f"Argument parsing error: {e}")

        # calling tool
        result = tool(**parsed_kwargs)

        if isinstance(result, FailedToolResult):
            return result

        # now we have a success
        if self.hook_caller is not None:
            err = self.hook_caller.run_after(kwargs["agent"], tool_name)
            if isinstance(err, FailedToolResult):
                return FailedToolResult(
                    f"Hooks for {tool_name!r} raised an error : {err.txt}"
                )

        if isinstance(result, (SuccessToolResult, FailedToolResult)):
            return result

        raise TypeError(
            f"Tool {tool.__name__} returned unexpected type: {type(result)}. "
            "Expected SuccessToolResult or FailedToolResult."
        )
