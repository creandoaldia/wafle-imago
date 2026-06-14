"""NVIDIA NIM backend — free, 1k req/month, no credit card needed.

Uses NVIDIA Cloud Functions (NVCF) API:
  POST https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/{function_id}
  Authorization: Bearer {NVIDIA_API_KEY}
  Body: {"prompt": "...", "width": 1024, "height": 1024, "steps": 4}
  Response: {"artifacts": [{"base64": "...", "type": "image/png"}]}
"""

import base64
import json
import os
import time
import urllib.request
import ssl
from pathlib import Path
from typing import Any

from .base import BaseBackend, GenerationResult, BACKENDS


NVCF_BASE = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions"
NVCF_MODELS = {
    "flux-schnell": ("105fe02c-924b-4dfa-9797-92d89c3936ad", "FLUX.1 Schnell"),
    "flux-1-dev": ("0c474133-6fd2-42f6-be29-8ebbbaeaaeb2", "FLUX.1 Dev"),
    "flux-2-klein-4b": ("f67e96d8-1c4e-422e-a913-90f00e19aa9a", "FLUX.2 Klein 4B"),
}


class NvidiaBackend(BaseBackend):
    name = "nvidia"
    priority = 5

    def _get_token(self) -> str | None:
        if t := os.getenv("NVIDIA_API_KEY"):
            return t
        env_path = Path(r"C:\web-ai-lab\.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("NVIDIA_API_KEY="):
                    parts = line.split("=", 1)
                    if len(parts) == 2 and parts[1].strip():
                        return parts[1].strip()
        return None

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        token = self._get_token()
        if not token:
            return GenerationResult(
                success=False,
                error="NVIDIA_API_KEY required. "
                      "Get a free key at https://build.nvidia.com (no credit card needed, 1k req/month free).",
            )

        model_key = kwargs.get("model", "flux-schnell")
        func_info = NVCF_MODELS.get(model_key)
        if not func_info:
            func_info = NVCF_MODELS["flux-schnell"]
        func_id, model_name = func_info

        url = f"{NVCF_BASE}/{func_id}"
        body = json.dumps({
            "prompt": prompt,
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 1024),
            "steps": min(kwargs.get("steps", 4), 8),
        }).encode()

        t0 = time.time()
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                url, data=body,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                resp = json.loads(r.read())

            elapsed = round(time.time() - t0, 1)

            artifacts = resp.get("artifacts", [])
            for art in artifacts:
                b64 = art.get("base64", "")
                if b64:
                    data = base64.b64decode(b64)
                    fmt = "image/png"
                    if art.get("type") == "image/jpeg":
                        fmt = "image/jpeg"
                    return GenerationResult(
                        success=True, data=data, format=fmt,
                        time_seconds=elapsed, model=model_key,
                    )

            return GenerationResult(
                success=False, error="No image artifacts in response",
                time_seconds=elapsed,
            )
        except urllib.error.HTTPError as e:
            elapsed = round(time.time() - t0, 1)
            error_body = e.read().decode(errors="replace")[:300]
            return GenerationResult(
                success=False,
                error=f"HTTP {e.code}: {error_body}",
                time_seconds=elapsed,
            )
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            return GenerationResult(
                success=False, error=str(e)[:300],
                time_seconds=elapsed,
            )

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": "flux-schnell", "name": "FLUX.1 Schnell (NVCF)", "cost": 0, "type": "image"},
            {"id": "flux-1-dev", "name": "FLUX.1 Dev (NVCF)", "cost": 0, "type": "image"},
            {"id": "flux-2-klein-4b", "name": "FLUX.2 Klein 4B (NVCF)", "cost": 0, "type": "image"},
        ]


BACKENDS["nvidia"] = NvidiaBackend
