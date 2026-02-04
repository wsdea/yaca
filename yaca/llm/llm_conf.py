from enum import StrEnum


class LLMModel(StrEnum):
    GPT52 = "gpt-5.2-2025-12-11"
    CODEX = "gpt-5.2-codex"


MAX_INPUT_TOKENS_PER_MODEL = {
    LLMModel.GPT52: 400000,
    LLMModel.CODEX: 400000,
}


LLM_TIMEOUT = 120
