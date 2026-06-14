"""Cloudflare Workers AI backend — free, 10k neurons/day, no credit card needed."""

import base64
import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

from .base import BaseBackend, GenerationResult, BACKENDS


CF_BASE = "https://api.cloudflare.com/client/v4/accounts"
CF_MODELS = {
    "flux-schnell": "@cf/black-forest-labs/flux-1-schnell",
    "flux-2-klein-4b": "@cf/black-forest-labs/flux-2-klein-4b",
    "flux-2-klein-9b": "@cf/black-forest-labs/flux-2-klein-9b",
    "sdxl": "@cf/stabilityai/stable-diffusion-xl-base-1.0",
    "dreamshaper": "@cf/lykon/dreamshaper-8-lcm",
}


class CloudflareBackend(BaseBackend):
    name = "cloudflare"
    priority = 0

    def _get_creds(self) -> tuple[str, str] | None:
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if account_id and api_token:
            return account_id, api_token
        env_path = Path(r"C:\web-ai-lab\.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("CLOUDFLARE_ACCOUNT_ID="):
                    account_id = line.split("=", 1)[1].strip()
                elif line.startswith("CLOUDFLARE_API_TOKEN="):
                    api_token = line.split("=", 1)[1].strip()
        return (account_id, api_token) if account_id and api_token else None

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        creds = self._get_creds()
        if not creds:
            return GenerationResult(
                success=False,
                error="CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN required. "
                      "Sign up free at https://dash.cloudflare.com/sign-up/workers-and-pages (no credit card needed). "
                      "Then get your API token at https://dash.cloudflare.com/profile/api-tokens",
            )
        account_id, api_token = creds

        model_key = kwargs.get("model", "flux-schnell")
        cf_model = CF_MODELS.get(model_key)
        if not cf_model:
            cf_model = CF_MODELS["flux-schnell"]

        steps = min(kwargs.get("steps", 4), 8)
        seed = kwargs.get("seed", int(time.time()) % 2**31)

        url = f"{CF_BASE}/{account_id}/ai/run/{urllib.parse.quote(cf_model, safe='@/')}"
        body = json.dumps({"prompt": prompt, "steps": steps, "seed": seed}).encode()

        t0 = time.time()
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())

            elapsed = round(time.time() - t0, 1)

            if not resp.get("success"):
                err_msg = resp.get("errors", [{}])[0].get("message", "Unknown error")
                return GenerationResult(
                    success=False, error=err_msg, time_seconds=elapsed,
                )

            img_b64 = resp.get("result", {}).get("image")
            if not img_b64:
                return GenerationResult(
                    success=False, error="No image in response",
                    time_seconds=elapsed,
                )

            data = base64.b64decode(img_b64)
            return GenerationResult(
                success=True, data=data, format="image/jpeg",
                time_seconds=elapsed, model=model_key,
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
                success=False, error=str(e)[:300], time_seconds=elapsed,
            )

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": "flux-schnell", "name": "FLUX.1 Schnell (12B)", "cost": 0, "type": "image"},
            {"id": "flux-2-klein-4b", "name": "FLUX.2 Klein (4B)", "cost": 0, "type": "image"},
            {"id": "flux-2-klein-9b", "name": "FLUX.2 Klein (9B)", "cost": 0, "type": "image"},
            {"id": "sdxl", "name": "Stable Diffusion XL", "cost": 0, "type": "image"},
            {"id": "dreamshaper", "name": "DreamShaper 8 LCM", "cost": 0, "type": "image"},
        ]


BACKENDS["cloudflare"] = CloudflareBackend
