import os

import pytest

from yaca.config import get_cfg_value
from yaca.llm.litellm_client import LLMClient


def test_llm_smoke():
    api_key_env = get_cfg_value("llm.litellm.api_key_env", str)
    api_key = os.environ.get(api_key_env)
    if not api_key:
        pytest.skip(
            f"Skipping LLM smoke test: environment variable {api_key_env!r} is not set."
        )

    client = LLMClient()
    response = client("Reply with the single word: ping")

    assert isinstance(response, str)
    assert response.strip() != ""
    assert "ping" in response.lower()