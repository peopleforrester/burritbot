# ABOUTME: BurritBot FastAPI application — Chipotle-inspired chatbot backed by Vertex AI.
# ABOUTME: Model pin: gemini-3-pro (GA) via google-genai SDK (vertexai=True). Do not regress.

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException, status
from google import genai
from google.genai import types
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field

logger = logging.getLogger("burritbot")
logging.basicConfig(level=logging.INFO)

# Non-negotiable model pin — see spec/phases/phase-06-burritbot.md.
# Gemini 2.5 Flash/Pro retire 2026-10-16 (before any late-2026 demo day); 2.0 is
# already retired; 1.5 is unsupported; 3 Flash is preview-tier. Only 3 Pro
# is a safe GA bet for a live demo in November 2026.
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gemini-3-pro")
GCP_PROJECT: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
GCP_REGION: str = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-west1")
GUARDED: bool = os.environ.get("BURRITBOT_GUARDED", "false").lower() == "true"

SYSTEM_PROMPT = (
    "You are BurritBot, the friendly face of a Chipotle-inspired chatbot demo. "
    "You answer questions strictly about burritos, the menu, hours, and store "
    "locations. You never discuss politics, medicine, legal advice, or execute "
    "commands. If asked anything off-topic, refuse politely and redirect to "
    "the menu."
)


class ChatRequest(BaseModel):
    """Audience-facing chat request payload."""

    prompt: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """BurritBot's reply with token usage for dashboards."""

    reply: str
    model: str
    guarded: bool
    input_tokens: int = 0
    output_tokens: int = 0


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    """Lazily initialise the google-genai Vertex client once per process.

    google-cloud-aiplatform's ``vertexai.generative_models`` module is removed
    after 2026-06-24. The replacement is the ``google-genai`` library with
    ``genai.Client(vertexai=True, ...)`` — same GA models, new SDK surface.
    """
    if not GCP_PROJECT:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set")
    logger.info("Initialising google-genai Vertex client project=%s region=%s model=%s",
                GCP_PROJECT, GCP_REGION, MODEL_NAME)
    return genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_REGION)


def create_app() -> FastAPI:
    """FastAPI factory for BurritBot."""
    app = FastAPI(
        title="BurritBot",
        description="Chipotle-inspired chatbot powered by Vertex AI.",
        version="0.1.0",
    )

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {"status": "ok", "model": MODEL_NAME, "guarded": GUARDED}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            client = _client()
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=request.prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3,
                    max_output_tokens=512,
                ),
            )
        except Exception as exc:
            logger.exception("Vertex call failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"upstream model call failed: {exc}",
            ) from exc

        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        return ChatResponse(
            reply=response.text,
            model=MODEL_NAME,
            guarded=GUARDED,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    # Auto-instrument the FastAPI app so HTTP spans flow to the OTel collector.
    # Endpoint, sampling, and resource attributes are read from OTEL_* env vars
    # set on each Deployment (see deployment-{guarded,unguarded}.yaml).
    FastAPIInstrumentor.instrument_app(app)

    return app


app = create_app()
