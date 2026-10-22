"""Send one prompt to the model (or to the mock) and return a plain record of what happened.

Every call is a separate request with no conversation history, so the model never
sees other items, the original sentence, or the condition label.
"""

import json
from datetime import datetime, timezone

from .config import ModelSettings
from .masking import MASK_CHAR
from .prompts import RESPONSE_SCHEMA


class FatalAPIError(RuntimeError):
    """An error that will affect every request (bad key, unknown model), so the run should stop."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AnthropicClient:
    def __init__(self, settings: ModelSettings):
        import anthropic  # imported here so mock mode and tests work without the package configured

        self._anthropic = anthropic
        self.settings = settings
        self.client = anthropic.Anthropic(max_retries=3)

    def request_params(self, prompt: str) -> dict:
        # Sampling parameters (temperature etc.) are not accepted by current Claude models,
        # so outputs can vary between runs. The cache keeps the single response we analyze.
        return {
            "model": self.settings.model,
            "max_tokens": self.settings.max_tokens,
            "output_config": {
                "effort": self.settings.effort,
                "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA},
            },
            "messages": [{"role": "user", "content": prompt}],
        }

    def send(self, prompt: str) -> dict:
        anthropic = self._anthropic
        params = self.request_params(prompt)
        record = {"request": params, "requested_at": utc_now()}
        try:
            response = self.client.messages.create(**params)
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError) as e:
            raise FatalAPIError(f"{type(e).__name__}: {e.message}") from e
        except anthropic.APIStatusError as e:
            return {**record, "status": "api_error", "error": f"{type(e).__name__} ({e.status_code}): {e.message}",
                    "received_at": utc_now()}
        except anthropic.APIConnectionError as e:
            return {**record, "status": "api_error", "error": f"{type(e).__name__}: {e}", "received_at": utc_now()}

        text = "".join(block.text for block in response.content if block.type == "text")
        return {
            **record,
            "status": "ok",
            "received_at": utc_now(),
            "response_id": response.id,
            "response_model": response.model,
            "stop_reason": response.stop_reason,
            "stop_details": response.stop_details.model_dump() if getattr(response, "stop_details", None) else None,
            "usage": response.usage.model_dump() if response.usage else None,
            "raw_text": text,
        }


class MockClient:
    """A stand-in for pipeline testing. It is NOT a language model and its output means nothing.

    It returns intact sentences unchanged and fills every blank with the letter 'e'.
    """

    def __init__(self, settings: ModelSettings):
        self.settings = settings

    def send(self, prompt: str) -> dict:
        sentence = prompt.split("<sentence>", 1)[1].rsplit("</sentence>", 1)[0]
        record = {"request": {"mock": True, "prompt": prompt}, "requested_at": utc_now()}
        return {
            **record,
            "status": "ok",
            "received_at": utc_now(),
            "response_id": "mock",
            "response_model": self.settings.model,
            "stop_reason": "end_turn",
            "stop_details": None,
            "usage": None,
            "raw_text": json.dumps({"reconstruction": sentence.replace(MASK_CHAR, "e")}),
        }


def make_client(settings: ModelSettings, mock: bool):
    return MockClient(settings) if mock else AnthropicClient(settings)
