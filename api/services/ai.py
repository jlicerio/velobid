import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIConnectionError

load_dotenv()

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENCODE_API_KEY"),
    base_url=os.getenv("OPENCODE_BASE_URL"),
    http_client=httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0)),
    max_retries=2,
)

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

SYSTEM_PROMPT = """\
You are an expert construction estimator and project manager.
Your task is to refine or modify a project configuration JSON based on user instructions.
You MUST return ONLY the updated JSON object. No preamble, no explanation, no markdown blocks.
Ensure the JSON is valid and preserves the existing structure unless explicitly told to change it.
"""


def check_llm_health() -> None:
    """Check if the LLM endpoint is reachable. Raises APIConnectionError if not."""
    try:
        base_url = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
        with httpx.Client(timeout=httpx.Timeout(connect=5.0, read=5.0)) as health_client:
            health_client.get(base_url)
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("LLM health check failed - endpoint unreachable: %s", exc)
        raise APIConnectionError(message=f"LLM endpoint unreachable: {exc}") from exc


def refine_config(current_config: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Use DeepSeek to refine a project or trade configuration."""
    user_message = (
        f"Current Config:\n{json.dumps(current_config, indent=2)}\n\nInstructions:\n{prompt}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            timeout=30.0,
        )
    except APITimeoutError:
        logger.error("LLM request timed out after 30s")
        raise
    except APIConnectionError:
        logger.error("LLM connection failed")
        raise

    content = response.choices[0].message.content.strip()
    # Handle potential markdown wrappers if the LLM ignores the system prompt
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:].strip()

    return json.loads(content)

