import base64
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib import error, parse, request

from ..config.settings import ModelConfig


class OpenAICompatibleAPIEngine:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.api_base_url = self._validate_api_base_url(config.api_base_url)
        if not config.api_key_env:
            raise ValueError("api_key_env is required for openai_compatible backend")

        self.api_key = os.environ.get(config.api_key_env)
        if not self.api_key:
            raise ValueError(f"Environment variable {config.api_key_env} is not set")

    def _validate_api_base_url(self, api_base_url: str | None) -> str:
        if not api_base_url:
            raise ValueError("api_base_url is required for openai_compatible backend")

        parsed = parse.urlparse(api_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "api_base_url must be a valid http(s) URL for openai_compatible backend"
            )
        return api_base_url.rstrip("/")

    def _encode_image_as_data_url(self, image_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        data = Path(image_path).read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _convert_image_source(self, source: str) -> str:
        parsed = parse.urlparse(source)
        if parsed.scheme in {"http", "https", "data"}:
            return source
        return self._encode_image_as_data_url(source)

    def _build_payload(self, inputs_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        converted_messages = []
        for message in inputs_messages:
            converted_content = []
            for item in message.get("content", []):
                if item.get("type") == "text":
                    converted_content.append({"type": "text", "text": item["text"]})
                    continue

                if item.get("type") != "image_url":
                    continue

                source = item.get("image")
                if source is None:
                    source = item.get("image_url", {}).get("url")
                if not source:
                    raise ValueError(
                        "image_url content item is missing an image source"
                    )

                converted_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": self._convert_image_source(source)},
                    }
                )

            converted_messages.append(
                {"role": message["role"], "content": converted_content}
            )

        return {
            "model": self.config.name,
            "messages": converted_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_new_tokens,
        }

    def _extract_text(self, response_data: Dict[str, Any]) -> str:
        try:
            choices = response_data["choices"]
            first_choice = choices[0]
            message = first_choice["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "Malformed chat completion response: "
                f"{self._format_response_context(response_data)}"
            ) from exc

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if not isinstance(item, dict):
                    raise RuntimeError(
                        "Malformed chat completion response: "
                        f"{self._format_response_context(response_data)}"
                    )
                if item.get("type") == "text":
                    text = item.get("text")
                    if not isinstance(text, str):
                        raise RuntimeError(
                            "Malformed chat completion response: "
                            f"{self._format_response_context(response_data)}"
                        )
                    text_parts.append(text)

            if text_parts:
                return "".join(text_parts)

        raise RuntimeError(
            "Malformed chat completion response: "
            f"{self._format_response_context(response_data)}"
        )

    def _format_response_context(self, response_data: Dict[str, Any]) -> str:
        context = json.dumps(response_data, ensure_ascii=True, default=str)
        if len(context) > 300:
            context = f"{context[:300]}..."
        return context

    def _request_once(self, req: request.Request) -> Dict[str, Any]:
        with request.urlopen(req, timeout=self.config.api_timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:
        payload = self._build_payload(inputs_messages)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.api_base_url}/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        max_attempts = self.config.api_max_retries + 1
        for attempt in range(max_attempts):
            try:
                data = self._request_once(req)
                break
            except error.HTTPError as exc:
                response_body = exc.read().decode("utf-8", errors="replace")
                is_transient = exc.code == 429 or 500 <= exc.code < 600
                if is_transient and attempt + 1 < max_attempts:
                    time.sleep(0.1)
                    continue
                raise RuntimeError(
                    f"API request failed with HTTP {exc.code}: {response_body}"
                ) from exc
            except error.URLError as exc:
                if attempt + 1 < max_attempts:
                    time.sleep(0.1)
                    continue
                raise RuntimeError(f"API request failed: {exc.reason}") from exc

        return self._extract_text(data)
