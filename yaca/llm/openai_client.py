import glob
import hashlib
import json
import os
import time
from threading import Lock

from openai import APIConnectionError, AuthenticationError, OpenAI

from ..logger import get_logger
from .json import load_json, save_json
from .llm_conf import MAX_INPUT_TOKENS_PER_MODEL, LLMModel
from .messages import Message

logger = get_logger(__name__)

GLOBAL_COUNT = 0


class LLMError(Exception):
    pass


class TokenRefreshError(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        model_name=LLMModel.GPT52,
        llm_debug_folder=None,
        llm_cache_dir=None,
    ):
        self.model_name = model_name
        self.max_input_tokens = MAX_INPUT_TOKENS_PER_MODEL[self.model_name]

        # Openai
        self.openai_base_url = None
        self.openai_api_key = os.environ["OPENAI_API_KEY"]
        self.openai_org_id = os.environ["OPENAI_ORG_ID"]
        self.openai_client = OpenAI(
            api_key=self.openai_api_key,
            organization=self.openai_org_id,
            max_retries=5,
        )

        # Cache
        self.llm_clients_cache_dir = llm_cache_dir
        if self.llm_clients_cache_dir:
            self.llm_clients_cache_dir = os.path.abspath(self.llm_clients_cache_dir)
        self.init_get_cache()

        # Debug folder
        self.llm_debug_folder = llm_debug_folder
        if self.llm_debug_folder is not None:
            self.llm_debug_folder = os.path.abspath(self.llm_debug_folder)
            os.makedirs(self.llm_debug_folder, exist_ok=True)
            # clearing debug folder
            for x in glob.glob(os.path.join(self.llm_debug_folder, "*")):
                os.remove(x)

    def _get_cache_key(self, inputs: str, params: dict) -> str:
        """Generate a cache key using SHA256 hash"""
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
                logger.warning(
                    "Could not save cache as file is already being used, try again later"
                )

    def _load_cache_from_disk(self) -> dict:
        """Load cache data from file"""
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
                f"{self.__class__.__name__}_{str(self.model_name).replace('/', '-')}_{self.max_input_tokens}.json",
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
                f'text_inputs should be a string (the first message content), or a list of dict "role", "content" got {type(text_inputs)}'
            )
        return messages

    def _renew_token(self) -> None:
        pass

    # Chat Completion
    def _openai_chat_completion(self, text_inputs: str | list[dict]) -> dict:
        """returns a dict with the answer and the reasoning content"""
        messages = self.inputs_to_messages(text_inputs)

        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
        )

        response = response.choices[0].message
        try:
            reasoning = response.reasoning_content
        except AttributeError:
            # model doesn't support reasoning
            reasoning = ""

        return {
            "answer": response.content,
            "reasoning": reasoning,
        }

    def _chat_generate_text(self, text_inputs: str | list[dict]) -> dict:
        """Attempt to get a chat completion with retries.

        Retries up to 3 times on generic errors (e.g., 403 ext_authz_error).
        Sleeps with exponential backoff between attempts.
        """
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # First attempt (or retry) to get completion
                response = self._openai_chat_completion(text_inputs)
                return response
            except (AuthenticationError, APIConnectionError):
                # Token issues – try to refresh once and retry immediately
                logger.info("Chat Token expired, refreshing...")
                try:
                    self._renew_token()
                except Exception as e:
                    raise TokenRefreshError(f"Failed token refresh: {str(e)}")
                # After token refresh, continue to next iteration to retry
            except Exception as e:
                # For other errors (e.g., 403 ext_authz_error), decide whether to retry
                if attempt >= max_retries:
                    # No more retries left, raise the original error wrapped as LLMError
                    raise LLMError(e)
                else:
                    # Sleep with exponential backoff before next retry
                    backoff = 2 ** (attempt - 1)
                    logger.warning(
                        f"LLM call failed (attempt {attempt}/{max_retries}): {e}. "
                        f"Retrying after {backoff}s..."
                    )
                    time.sleep(backoff)
        # If we exit the loop without returning, raise a generic error
        raise LLMError("Failed to get chat completion after retries")

    def messages_to_dicts(self, messages: list[Message]):
        # merging consecutive messages if they are the same role
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
    ) -> str:
        if isinstance(text_inputs, list):
            text_inputs = self.messages_to_dicts(text_inputs)

        result = None
        if self.cache_file:
            key = self._get_cache_key((text_inputs,), {})
            result = self._get_from_cache(key)

            if isinstance(result, str):
                # for backward compatibility
                result = {"reasoning": "", "answer": result}
                self._set_cache_key(key, result)

        if result is None:
            try:
                # here result is a dict with the answer and reasoning (if applicable)
                result = self._chat_generate_text(text_inputs=text_inputs, **kwargs)
            except Exception as e:
                logger.error(f"LLM call failed for {self.__class__.__name__}. {e}")
                raise LLMError(e)

            if self.cache_file:
                self._set_cache_key(key, result)

        global GLOBAL_COUNT
        if self.llm_debug_folder is not None:
            # logging both reasoning and response
            file = os.path.join(
                self.llm_debug_folder, f"llm_log_{int(time.time())}-{GLOBAL_COUNT}.txt"
            )
            if isinstance(text_inputs, list):
                text_inputs = "\n".join(
                    [
                        f"\n\n**{dic['role']}**\n\n{dic['content']}"
                        for dic in text_inputs
                    ]
                )
            with open(file, "w", encoding="utf-8") as f:
                f.write(
                    f"{text_inputs}\n\n\n\n{'=' * 30}\nReasoning:\n{'=' * 30}\n\n{result['reasoning']}\n\n\n\n{'=' * 30}\nAnswer:\n{'=' * 30}\n\n{result['answer']}"
                )
            GLOBAL_COUNT += 1

        if hide_reasoning:
            return result["answer"] or ""
        else:
            return result
