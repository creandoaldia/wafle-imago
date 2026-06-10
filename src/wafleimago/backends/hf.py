"""HuggingFace Inference Providers backend — fallback option."""

import time
import io
import os
from pathlib import Path
from typing import Any

from huggingface_hub import InferenceClient

from .base import BaseBackend, GenerationResult, BACKENDS


HF_MODELS = {
    "flux-schnell": "black-forest-labs/FLUX.1-schnell",
    "flux-dev": "black-forest-labs/FLUX.1-dev",
    "sdxl-turbo": "stabilityai/sdxl-turbo",
    "sd-3.5-turbo": "stabilityai/stable-diffusion-3.5-turbo",
}


class HFBackend(BaseBackend):
    name = "hf"
    priority = 20

    def _get_token(self) -> str | None:
        if t := os.getenv("HF_TOKEN"):
            return t
        env_path = Path(r"C:\web-ai-lab\.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("HF_TOKEN=") and "=" in line:
                    val = line.split("=", 1)[1].strip()
                    if val:
                        return val
        return None

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        model = kwargs.get("model", "flux-schnell")
        hf_model = HF_MODELS.get(model)
        if not hf_model:
            return GenerationResult(success=False, error=f"Modelo no válido: {model}")

        token = self._get_token()
        if not token:
            return GenerationResult(success=False, error="HF_TOKEN no configurado")

        client = InferenceClient(api_key=token)
        t0 = time.time()

        try:
            image = client.text_to_image(
                prompt=prompt,
                model=hf_model,
                width=kwargs.get("width", 1024),
                height=kwargs.get("height", 1024),
            )
            elapsed = round(time.time() - t0, 1)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            return GenerationResult(
                success=True, data=buf.getvalue(),
                format="image/png", time_seconds=elapsed, model=model,
            )
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            return GenerationResult(
                success=False, error=str(e)[:300], time_seconds=elapsed
            )

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": k, "name": v, "cost": 0, "type": "image"}
            for k, v in HF_MODELS.items()
        ]


BACKENDS["hf"] = HFBackend
