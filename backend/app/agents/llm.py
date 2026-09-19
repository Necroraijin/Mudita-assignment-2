import json
import re
import time
import structlog
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
from pydantic import BaseModel
from app.config import get_settings

logger = structlog.get_logger()

# Pattern to strip API keys / tokens from log output
SECRET_PATTERN = re.compile(
    r"(AIza[a-zA-Z0-9\-_]{35}|Bearer\s+[a-zA-Z0-9\-_.]+)", re.IGNORECASE
)

_vertex_initialized = False


def _ensure_vertex_init():
    """Initialize Vertex AI SDK once per process."""
    global _vertex_initialized
    if not _vertex_initialized:
        settings = get_settings()
        vertexai.init(
            project=settings.gcp_project_id,
            location=settings.vertex_ai_location,
        )
        _vertex_initialized = True


def strip_secrets(text: str) -> str:
    return SECRET_PATTERN.sub("[REDACTED]", text)


class LLMResponse(BaseModel):
    content: str
    tokens_in: int
    tokens_out: int
    latency_ms: int


def call_llm(
    system_prompt: str,
    user_prompt: str,
    run_id: str,
    agent_name: str,
    step: str = "default",
) -> LLMResponse:
    settings = get_settings()
    _ensure_vertex_init()

    model = GenerativeModel(
        model_name=settings.vertex_ai_model,
        system_instruction=system_prompt,
    )

    generation_config = GenerationConfig(
        max_output_tokens=8192,
        temperature=0.1,
    )

    start_time = time.time()

    response = model.generate_content(
        user_prompt,
        generation_config=generation_config,
    )

    latency_ms = int((time.time() - start_time) * 1000)
    content = response.text

    # Extract token usage from usage metadata
    usage = response.usage_metadata
    tokens_in = usage.prompt_token_count if usage else 0
    tokens_out = usage.candidates_token_count if usage else 0

    logger.info(
        "llm_call_completed",
        run_id=run_id,
        agent=agent_name,
        step=step,
        model=settings.vertex_ai_model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        prompt_preview=strip_secrets(user_prompt[:200]),
        response_preview=strip_secrets(content[:200]),
    )

    return LLMResponse(
        content=content,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
    )


def parse_json_response(content: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    content = content.strip()

    # Try to extract from markdown code block
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()

    return json.loads(content)
