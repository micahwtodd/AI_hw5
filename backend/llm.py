"""Locked-down Portkey model configuration for every Campus Customs agent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from httpx2 import AsyncClient, ByteStream, Request
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

ROOT = Path(__file__).resolve().parent.parent
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
MODEL_NAME = "gpt-6-luna"


def get_portkey_api_key() -> str:
    """Load the key at runtime without printing, logging, or returning it elsewhere."""
    key = os.environ.get("PORTKEY_API_KEY", "").strip()
    if not key:
        for path in (ROOT / ".env", ROOT / "backend" / ".env"):
            if path.is_file():
                key = (dotenv_values(path).get("PORTKEY_API_KEY") or "").strip()
                if key:
                    break
    if not key or key == "your_key_here":
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Add it to a local .env file or environment "
            "variable; never paste the key into source, prompts, or chat."
        )
    return key


def _azure_item_id(raw: str, prefix: str) -> str:
    """Give a gateway id the prefix Azure's Responses API requires."""
    if raw.startswith(prefix):
        return raw
    suffix = "".join(character for character in raw.removeprefix("portkey_cache_") if character.isalnum())
    return f"{prefix}_{suffix or 'item'}"


def repair_responses_input(payload: dict[str, Any]) -> bool:
    """Rewrite Portkey cache ids so a tool follow-up is a legal Azure request.

    Portkey returns function-call items whose ``id`` is ``portkey_cache_<uuid>``.
    The next Responses request replays that id. Azure rejects it unless the item
    id begins with ``fc`` and the matching ``call_id`` begins with ``call``.
    Responses are not stored, so these ids only have to be well formed and paired.
    """
    items = payload.get("input")
    if not isinstance(items, list):
        return False
    changed = False
    call_ids: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or item.get("type") != "function_call":
            continue
        raw_call = item.get("call_id")
        if isinstance(raw_call, str):
            fixed_call = _azure_item_id(raw_call, "call")
            if fixed_call != raw_call:
                call_ids[raw_call] = fixed_call
                item["call_id"] = fixed_call
                changed = True
        raw_id = item.get("id")
        if isinstance(raw_id, str):
            fixed_id = _azure_item_id(raw_id, "fc")
            if fixed_id != raw_id:
                item["id"] = fixed_id
                changed = True
    for item in items:
        if not isinstance(item, dict) or item.get("type") != "function_call_output":
            continue
        raw_call = item.get("call_id")
        if not isinstance(raw_call, str):
            continue
        fixed_call = call_ids.get(raw_call, _azure_item_id(raw_call, "call"))
        if fixed_call != raw_call:
            item["call_id"] = fixed_call
            changed = True
    return changed


async def _repair_responses_request(request: Request) -> None:
    if request.method != "POST" or not request.url.path.rstrip("/").endswith("responses"):
        return
    payload = json.loads((await request.aread()).decode("utf-8"))
    if not isinstance(payload, dict) or not repair_responses_input(payload):
        return
    body = json.dumps(payload).encode("utf-8")
    request.stream = ByteStream(body)
    request._content = body
    request.headers["content-length"] = str(len(body))


def make_model() -> OpenAIResponsesModel:
    """Create the only model configuration allowed for this homework."""
    client = AsyncOpenAI(
        base_url=PORTKEY_BASE_URL,
        api_key=get_portkey_api_key(),
        http_client=AsyncClient(event_hooks={"request": [_repair_responses_request]}),
    )
    return OpenAIResponsesModel(
        MODEL_NAME,
        provider=OpenAIProvider(openai_client=client),
        profile=OpenAIModelProfile(openai_supports_strict_tool_definition=False),
        settings=OpenAIResponsesModelSettings(
            openai_reasoning_effort="none",
            openai_store=False,
        ),
    )
