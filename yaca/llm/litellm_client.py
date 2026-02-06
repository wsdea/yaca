import glob
import hashlib
import json
import os
import time
from threading import Lock

import litellm

from ..config import get_cfg_value
from .json import load_json, save_json
from .messages import Message

GLOBAL_COUNT = 0


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        model_name: str | None = None,
        llm_debug_folder=None,
        llm_cache_dir=None,
    ):
        if model_name is None:
            model_name = get_cfg_value("llm.model", str)

        self.model_name = model_name

        self.max_retries = get_cfg_value("llm.max_retries", int)
        self.timeout_seconds = get_cfg_value("llm.timeout_seconds", int)

        self.api_key_env = get_cfg_value("llm.api_key_env", str)
        self.api_key = os.environ.get(self.api_key_env)

        self.base_url = get_cfg_value("llm.base_url")
        if self.base_url is not None and not isinstance(self.base_url, str):
            raise Exception(
                f"Error parsing config. Expected 'llm.base_url' to be a string or null, but got {type(self.base_url)} instead"
            )
        self.llm_clients_cache_dir = llm_cache_dir
        if self.llm_clients_cache_dir:
            self.llm_clients_cache_dir = os.path.abspath(self.llm_clients_cache_dir)
        self.init_get_cache()

        self.llm_debug_folder = llm_debug_folder
        if self.llm_debug_folder is not None:
            self.llm_debug_folder = os.path.abspath(self.llm_debug_folder)
            os.makedirs(self.llm_debug_folder, exist_ok=True)
            for x in glob.glob(os.path.join(self.llm_debug_folder, "*")):
                os.remove(x)

    def _get_cache_key(self, inputs, params: dict) -> str:
        data = {"inputs": inputs, "params": params}
        cache_key_data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(cache_key_data.encode()).hexdigest()

    def _get_from_cache(self, key):
        with self.cache_lock:
            return self.cache_data.get(key)

    def _set_cache_key(self, key, value):
        with self.cache_lock:
            self.cache_data[key] = value

            try:
                save_json(self.cache_file, self.cache_data)
            except PermissionError:
                pass

    def _load_cache_from_disk(self) -> dict:
        with self.cache_lock:
            if os.path.exists(self.cache_file):
                self.cache_data = load_json(self.cache_file)
            else:
                self.cache_data = {}

    def init_get_cache(self):
        if self.llm_clients_cache_dir is None:
            self.cache_file = None
        else:
            self.cache_file = os.path.join(
                self.llm_clients_cache_dir,
                f"{self.__class__.__name__}_{str(self.model_name).replace('/', '-')}.json",
            )
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            self.cache_lock = Lock()
            self._load_cache_from_disk()

    def inputs_to_messages(self, text_inputs):
        if isinstance(text_inputs, str):
            messages = [{"role": "user", "content": text_inputs}]
        elif isinstance(text_inputs, list):
            for dic in text_inputs:
                assert isinstance(
                    dic, dict
                ), "type of text_inputs should be a list of dict with 'role' and 'content' keys"
                assert dic.get("role") in [
                    "user",
                    "system",
                    "assistant",
                ], f"{dic.get('role')} should be one of ['user', 'system', 'assistant']"
                assert isinstance(dic.get("content"), str), "Content should be string"

            messages = text_inputs
        else:
            raise Exception(
                f"text_inputs should be a string (the first message content), or a list of dict with 'role' and 'content' keys got {type(text_inputs)}"
            )
        return messages

    def _chat_completion(self, text_inputs: str | list[dict]) -> dict:
        messages = self.inputs_to_messages(text_inputs)

        params = {
            "model": self.model_name,
            "messages": messages,
            "timeout": self.timeout_seconds,
            "num_retries": self.max_retries,
        }

        if self.base_url is not None:
            params["api_base"] = self.base_url

        if self.api_key is not None:
            params["api_key"] = self.api_key

        try:
            response = litellm.completion(**params)
        except Exception as e:
            raise LLMError(e)

        try:
            message = response.choices[0].message
            content = message.content
        except Exception as e:
            raise LLMError(f"Unexpected LiteLLM response shape: {str(e)}")

        reasoning = ""
        if hasattr(message, "reasoning_content"):
            reasoning = message.reasoning_content or ""

        return {"answer": content or "", "reasoning": reasoning}

    def messages_to_dicts(self, messages: list[Message]):
        messages_dict = [x.to_dict() for x in messages if x]
        new_messages_dict = [messages_dict[0]]
        current_role = messages_dict[0]["role"]
        for x in messages_dict[1:]:
            if x["role"] == current_role:
                new_messages_dict[-1]["content"] += "\n\n" + x["content"]
            else:
                new_messages_dict.append(x)
            current_role = x["role"]

        return new_messages_dict

    def __call__(
        self,
        text_inputs: str | list[Message],
        hide_reasoning=True,
        **kwargs,
    ):
        if isinstance(text_inputs, list):
            text_inputs = self.messages_to_dicts(text_inputs)

        result = None
        if self.cache_file:
            key = self._get_cache_key((text_inputs,), {})
            result = self._get_from_cache(key)

            if isinstance(result, str):
                result = {"reasoning": "", "answer": result}
                self._set_cache_key(key, result)

        if result is None:
            result = self._chat_completion(text_inputs=text_inputs)

            if self.cache_file:
                self._set_cache_key(key, result)

        global GLOBAL_COUNT
        if self.llm_debug_folder is not None:
            file = os.path.join(
                self.llm_debug_folder, f"llm_log_{int(time.time())}-{GLOBAL_COUNT}.txt"
            )
            debug_inputs = text_inputs
            if isinstance(debug_inputs, list):
                debug_inputs = "\n".join(
                    [
                        f"\n\n**{dic['role']}**\n\n{dic['content']}"
                        for dic in debug_inputs
                    ]
                )
            with open(file, "w", encoding="utf-8") as f:
                f.write(
                    f"{debug_inputs}\n\n\n\n{'=' * 30}\nReasoning:\n{'=' * 30}\n\n{result['reasoning']}\n\n\n\n{'=' * 30}\nAnswer:\n{'=' * 30}\n\n{result['answer']}"
                )
            GLOBAL_COUNT += 1

        if hide_reasoning:
            return result["answer"] or ""
        else:
            return result
