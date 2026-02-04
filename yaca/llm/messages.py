class Message:
    def __init__(self, txt):
        self.txt = txt or ""
        self.tool_name = None

    def display_txt(self):
        return self.txt

    def __bool__(self):
        return bool(self.txt.strip())

    def __repr__(self):
        return "\n".join(
            [
                f"<{self.__class__.__name__}>",
                self.txt,
                f"</{self.__class__.__name__}>",
            ]
        )

    def to_dict(self):
        return {"role": self.role, "content": self.txt}


# abstract classes, should not be directly used
class _UserMessage(Message):
    role = "user"


class _AssistantMessage(Message):
    role = "assistant"


class _SystemMessage(Message):
    role = "system"


class _ToolResult(_UserMessage):
    """When model got a tool call response (success or not)"""


# Common Message classes
class UserInput(_UserMessage):
    """Each user message that is not modified by YACA"""


class FakeUserInput(UserInput):
    """Everytime we pretend the user said something, but it was an automated message like 'do the todo'"""

    def display_txt(self):
        return ""


class StarterPrompt(_SystemMessage):
    """System prompt dictating agent rules"""

    def display_txt(self):
        return ""


class AssistantReply(_AssistantMessage):
    """Each assistant message that is NOT a tool call attempt"""


class AttemptedToolCall(_AssistantMessage):
    """Each assistant message that is an attempt at calling a tool"""

    def display_txt(self):
        return ""


class FailedToolCall(_UserMessage):
    """When model failed to properly call a tool"""

    def display_txt(self):
        return "Error trying to call a tool"


class SuccessToolResult(_ToolResult):
    """When model got a tool call success"""

    def display_txt(self):
        return f"Called {self.tool_name}"


class AssistantResponse(SuccessToolResult):
    """When assistant thinks it finished the loop(ask_questions, reply_to_user, attempt_completion)"""

    def display_txt(self):
        return self.txt


class FailedToolResult(_ToolResult):
    """When model called a tool, but it returned a failure"""

    def display_txt(self):
        return f"Error calling {self.tool_name}"


class HelperMessage(_UserMessage):
    """Temp message added just one time to help the llm"""

    def display_txt(self):
        return ""


class DebugMessage(_UserMessage):
    """Message that should be shown to user, but not in the context"""

    def __init__(self, txt):
        self.debug_message = txt
        self.txt = ""  # it will be ignored in the context like so

    def display_txt(self):
        return self.debug_message
