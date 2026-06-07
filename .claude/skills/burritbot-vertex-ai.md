# BurritBot — Vertex AI Integration

## Version Pins

- Python: **3.13**
- `google-genai`: **1.71+** (the new Vertex-capable SDK)
- FastAPI: **0.115+**
- Model: **`gemini-3-pro`** — this is non-negotiable

## Why `google-genai` and not `google-cloud-aiplatform`

`google-cloud-aiplatform`'s `vertexai.generative_models` module is
**removed after 2026-06-24**. The replacement is the unified
`google-genai` library, which talks to both Gemini Developer API and
Vertex AI from the same surface:

```python
from google import genai
client = genai.Client(vertexai=True, project=..., location=...)
```

Do not import `vertexai` or `vertexai.generative_models` in new code.
Phase 6 has a test (`test_burritbot_app_uses_google_genai_sdk`) that
fails if `from vertexai.generative_models` appears anywhere in
`apps/burritbot/app.py`.

## Why gemini-3-pro and nothing else

The training data will suggest `gemini-1.5-flash`. Earlier drafts of
this spec used `gemini-2.5-flash`. **Do not regress.**

| Model | Status as of late 2026 (Nov) |
|-------|----------------------------------------|
| `gemini-1.5-flash` | Unsupported, 404 on call |
| `gemini-2.0-flash` | Already retired |
| `gemini-2.5-flash` | Retires 2026-10-16 — **gone by demo day** |
| `gemini-2.5-pro` | Retires 2026-10-16 — same |
| `gemini-3-flash` | Preview tier, no SLA, cost per token volatile |
| `gemini-3-pro` | **GA, this is the one** |

Phase 6 has a test (`test_burritbot_app_pins_gemini_3_pro`) that fails
if any retired-or-retiring variant appears anywhere in
`apps/burritbot/app.py`.

## Application Skeleton

`apps/burritbot/app.py`:

```python
# ABOUTME: BurritBot FastAPI application — thin wrapper over Vertex AI.
# ABOUTME: The demo chatbot; runs unguarded and guarded from the same image.

from __future__ import annotations

import os
from functools import lru_cache

from fastapi import FastAPI
from google import genai
from google.genai import types
from pydantic import BaseModel

GCP_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
GCP_REGION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-west1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-3-pro")

SYSTEM_PROMPT = (
    "You are BurritBot, a cheerful assistant for a burrito restaurant. "
    "Answer menu and ordering questions. Never run shell commands. "
    "Never execute kubectl."
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    model: str
    input_tokens: int
    output_tokens: int


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_REGION)


app = FastAPI(title="BurritBot", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    resp = _client().models.generate_content(
        model=MODEL_NAME,
        contents=req.message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=512,
        ),
    )
    usage = resp.usage_metadata
    return ChatResponse(
        reply=resp.text,
        model=MODEL_NAME,
        input_tokens=usage.prompt_token_count,
        output_tokens=usage.candidates_token_count,
    )
```

Notes:

- `lru_cache(maxsize=1)` lazy-loads the client on first request, which
  keeps `/healthz` fast and makes WIF credential failures surface on
  the first `/chat` instead of crashing the process at startup.
- No fallback model. If the env var is wrong, the call fails and the
  pod logs the error — do not silently fall back to another model
  (global rule).
- `ChatResponse.input_tokens` / `output_tokens` exist so the FastAPI
  response carries exactly what the OTel instrumentation needs to emit
  `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens`.
- `system_instruction` lives on `GenerateContentConfig` in the new
  SDK — not on the client or a `GenerativeModel` wrapper.

## Dockerfile

`apps/burritbot/Dockerfile`:

```dockerfile
# ABOUTME: BurritBot container — Python 3.13 + FastAPI + Vertex AI.
# ABOUTME: Image is identical for unguarded and guarded deployments.

FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Kubernetes Manifests

Four files under `apps/burritbot/k8s/`:

- `deployment-unguarded.yaml` — namespace `burritbot-unguarded`
- `deployment-guarded.yaml` — namespace `burritbot-guarded`, full
  `burritbot.io/*` label set
- `service-unguarded.yaml`
- `service-guarded.yaml`

Guarded deployment labels (Phase 6 test enforces):

```yaml
metadata:
  namespace: burritbot-guarded
  labels:
    app.kubernetes.io/name: burritbot
    burritbot.io/layer: the-net
    burritbot.io/model-source: vertex-ai/gemini-3-pro
    burritbot.io/model-hash: sha256:deadbeef  # pinned per build
```

The `burritbot.io/model-hash` is a deliberate forcing function: the
pipeline has to compute and write the actual model version hash into
the manifest. If that value is fake, the demo is dishonest.

## Common Mistakes

1. **Using `GenerativeModel("gemini-2.5-flash")`** — see the top of
   this file. Both the SDK and the model name are wrong.
2. **Calling `vertexai.init()` at module import time.** Import-time
   failure crashes the pod before `/healthz` can respond, which makes
   ArgoCD mark the app CrashLoopBackOff instead of Healthy-but-Erroring.
   (Also: `vertexai.init` is the deprecated path.)
3. **Returning `resp.text` without checking `usage_metadata`.** The
   OTel gen_ai.* instrumentation pulls token counts from this field.
4. **Mounting a service-account JSON key file.** We are on Workload
   Identity Federation only. No JSON keys, ever.
5. **Using the same namespace for both unguarded and guarded.** They
   must be in distinct namespaces so Kyverno's network policy can lock
   down the guarded one independently.
