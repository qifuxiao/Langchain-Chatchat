"""
OpenAI API Worker for Gitee and other OpenAI-compatible APIs.
"""
import json
import httpx
from typing import Dict, Iterator, List
from fastchat.conversation import Conversation
from fastchat import conversation as conv
from configs import logger, log_verbose
from server.model_workers.base import (
    ApiModelWorker,
    ApiChatParams,
    ApiEmbeddingsParams,
)


class OpenAIWorker(ApiModelWorker):
    """
    Worker for OpenAI-compatible APIs including Gitee AI.
    Supports chat, completion, and embeddings.
    """
    DEFAULT_EMBED_MODEL = "text-embedding-ada-002"  # Default, will be overridden by config

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = self.model_names[0] if self.model_names else None

    def do_chat(self, params: ApiChatParams) -> Iterator[Dict]:
        """
        Execute chat request to OpenAI-compatible API.
        """
        params.load_config(self.model_names[0])
        api_key = params.api_key or ""
        api_base_url = (params.api_base_url or "").rstrip("/")
        
        # Get the actual model name from config, not from params
        model_name = getattr(params, "model_name", None)
        if not model_name:
            # Try to get from worker config
            from server.utils import get_model_worker_config
            config = get_model_worker_config(self.model_names[0])
            model_name = config.get("model_name", self.model_names[0] if self.model_names else "gpt-3.5-turbo")

        url = f"{api_base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            "model": model_name,
            "messages": params.messages,
            "temperature": params.temperature,
            "stream": True,
        }
        if params.max_tokens is not None:
            data["max_tokens"] = params.max_tokens

        if log_verbose:
            logger.info(f"OpenAI chat request to {url} with model {model_name}")

        timeout_chat = getattr(params, "timeout", 120)
        try:
            answer = ""
            with httpx.Client(timeout=timeout_chat) as client, client.stream(
                    "POST", url, headers=headers, json=data
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    event = json.loads(payload)
                    choices = event.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {}).get("content")
                    if delta:
                        answer += delta
                        yield {"error_code": 0, "text": answer}

            if not answer:
                yield {"error_code": 500, "text": "OpenAI-compatible API returned no content."}
        except Exception as e:
            error_msg = f"OpenAI chat request failed: {e}"
            logger.error(error_msg)
            yield {
                "error_code": 500,
                "text": error_msg,
            }

    def do_embeddings(self, params: ApiEmbeddingsParams) -> Dict:
        """
        Execute embeddings request to OpenAI-compatible API.
        """
        params.load_config(self.model_names[0])
        api_key = params.api_key or ""
        api_base_url = (params.api_base_url or "").rstrip("/")
        embed_model = params.embed_model or self.DEFAULT_EMBED_MODEL

        url = f"{api_base_url}/embeddings"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        timeout = getattr(params, "timeout", 120)
        try:
            with httpx.Client(timeout=timeout) as client:
                results = []
                for text in params.texts:
                    data = {
                        "model": embed_model,
                        "input": text,
                    }
                    response = client.post(url, headers=headers, json=data)
                    response.raise_for_status()
                    result = response.json()

                    if "data" in result and len(result["data"]) > 0:
                        embedding = result["data"][0]["embedding"]
                        results.append(embedding)
                    else:
                        logger.error(f"Unexpected embedding response: {result}")
                        return {"code": 500, "msg": f"Unexpected embedding response: {result}"}

                return {
                    "code": 200,
                    "data": results,
                    "msg": "success",
                }
        except Exception as e:
            error_msg = f"OpenAI embeddings request failed: {e}"
            logger.error(error_msg)
            return {
                "code": 500,
                "msg": error_msg,
            }

    def make_conv_template(self, conv_template: str = None, model_path: str = None) -> Conversation:
        """
        Create conversation template for OpenAI-compatible APIs.
        """
        return conv.Conversation(
            name=self.model_names[0] if self.model_names else "openai",
            system_message="You are a helpful assistant.",
            messages=[],
            roles=["user", "assistant", "system"],
            sep="\n",
            stop_str=None,
            stop_token_ids=None,
        )

    def validate_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Validate and format messages for OpenAI API.
        """
        # OpenAI expects messages with 'role' and 'content'
        validated = []
        for msg in messages:
            if "role" in msg and "content" in msg:
                validated.append(msg)
            else:
                # Skip invalid messages
                continue
        return validated
