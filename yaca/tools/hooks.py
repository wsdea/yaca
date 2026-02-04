import yaml

from ..llm import FailedToolResult, SuccessToolResult
from ..llm.messages import DebugMessage
from .run_command import run_command_tool


class HookCaller:
    def __init__(self, hooks_path: str):
        self.hooks_path = hooks_path
        self.cfg = self.load()

        # checking syntax
        for tool in self.cfg:
            self.hooks_for_tool(tool)

    def load(self) -> dict:
        try:
            with open(self.hooks_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            data = {}

        if not isinstance(data, dict):
            data = {}

        self._config = data
        return self._config

    def hooks_for_tool(self, tool_name: str) -> list:
        hooks = self.cfg.get(tool_name, [])
        if hooks is None:
            return []
        if not isinstance(hooks, list):
            raise Exception(
                f"Failed to parse hooks.yaml, expecting a list of hook objects, got {hooks}"
            )

        parsed = []
        for hook in hooks:
            if not isinstance(hook, dict):
                raise Exception(
                    f"Failed to parse hooks.yaml, expecting a hook object like {{cmd, on_error}}, got {hook}"
                )

            cmd = hook.get("cmd")
            on_error = hook.get("on_error")

            if not isinstance(cmd, str) or not cmd.strip():
                raise Exception(
                    f"Failed to parse hooks.yaml, hook is missing non-empty 'cmd': {hook}"
                )
            if on_error not in ("blocking", "ignore"):
                raise Exception(
                    "Failed to parse hooks.yaml, hook is missing valid 'on_error' "
                    f"(blocking|ignore): {hook}"
                )

            parsed.append({"cmd": cmd.strip(), "on_error": on_error})

        return parsed

    def run_after(self, agent, tool_name: str) -> FailedToolResult | None:
        """Executes the hooks"""
        if agent._pytest:
            return

        hooks = self.hooks_for_tool(tool_name)
        if not hooks:
            return

        for hook in hooks:
            cmd = hook["cmd"]
            on_error = hook["on_error"]

            agent.status_message = f"Running hook {cmd}"
            agent.logger.debug(f"Running hook {cmd!r}")
            result = run_command_tool(agent, cmd)
            if not isinstance(result, SuccessToolResult):
                agent.logger.warning(f"Error running hook {cmd!r} : {result.txt}")

                if on_error == "ignore":
                    agent.status_message = f"Hook {cmd} failed, skipping"
                    agent.append_message(
                        DebugMessage(
                            f"Warning, hook for {tool_name!r} ({cmd}) failed : {result.txt!r}"
                        )
                    )
                    continue

                return FailedToolResult(result.txt)

        return
