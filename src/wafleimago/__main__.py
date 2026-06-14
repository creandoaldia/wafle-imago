"""Wafle-Imago — universal MCP server for AI image generation.

Usage:
  wafle-imago                          # Start MCP server (stdio)
  wafle-imago --backend hf             # Use HuggingFace backend
  wafle-imago --http --port 8000       # HTTP mode
  wafle-imago --version                # Version
"""

import argparse
import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import __version__
from .backends.base import BACKENDS
from .backends.pollinations import PollinationsBackend
from .backends.hf import HFBackend
from .backends.cloudflare import CloudflareBackend
from .backends.nvidia import NvidiaBackend
from .security.validator import validate_prompt, RateLimiter
from .security.logger import AuditLogger

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("wafle-imago")

PollinationsBackend()
HFBackend()
CloudflareBackend()
NvidiaBackend()


def _resolve_save_dir(save_path: str, prompt: str) -> Path:
    if save_path:
        target = Path(save_path)
    else:
        target = Path.cwd() / "public" / "assets" / "images"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _slugify(text: str, max_words: int = 3) -> str:
    import re
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return "-".join(words[:max_words])[:50].rstrip("-")


def create_mcp(backend_name: str = "cloudflare") -> FastMCP:
    mcp = FastMCP("wafle-imago")
    audit = AuditLogger()
    rate_limiter = RateLimiter()

    backend = BACKENDS.get(backend_name)
    if not backend:
        logger.error("Backend %s not found, using cloudflare")
        backend = BACKENDS["cloudflare"]

    backend_instance = backend()

    @mcp.tool()
    async def generate_image(
        prompt: str,
        model: str = "",
        width: int = 1024,
        height: int = 1024,
        save_path: str = "",
        filename: str = "",
        safe: bool = True,
    ) -> str:
        """Generate an image from a text prompt.

        Args:
            prompt: Detailed image description (7-layer prompt recommended)
            model: Model to use. Empty = auto/default. Options: flux, gptimage, seedream, zimage, flux-schnell, etc.
            width: Image width in pixels
            height: Image height in pixels
            save_path: Directory to save the image (default: cwd/public/assets/images/)
            filename: Custom filename (without extension). Auto-generated if empty.
            safe: Enable content safety filters (default: true)
        """
        val = validate_prompt(prompt, strict=safe)
        if not val.valid and safe:
            return json.dumps({
                "success": False,
                "risk": val.risk,
                "reason": val.reason,
            })

        ok, limit_reason = rate_limiter.check()
        if not ok:
            return json.dumps({"success": False, "error": limit_reason})

        save_dir = _resolve_save_dir(save_path, prompt)
        fname = filename or f"{_slugify(prompt)}-{model or 'auto'}-{width}x{height}.png"

        result = backend_instance.generate(
            prompt=val.sanitized_prompt or prompt,
            model=model,
            width=width,
            height=height,
            safe=safe,
        )

        audit.generation(
            model=result.model,
            prompt=prompt,
            success=result.success,
            time_s=result.time_seconds,
            backend=backend_instance.name,
            size_bytes=len(result.data) if result.data else 0,
            risk=val.risk,
        )

        if not result.success or not result.data:
            return json.dumps({
                "success": False,
                "error": result.error,
                "model": result.model,
                "time_seconds": result.time_seconds,
            })

        filepath = save_dir / fname
        filepath.write_bytes(result.data)
        img_b64 = base64.b64encode(result.data).decode("utf-8")

        return json.dumps({
            "success": True,
            "model": result.model,
            "backend": backend_instance.name,
            "width": width,
            "height": height,
            "time_seconds": result.time_seconds,
            "format": result.format,
            "path": str(filepath),
            "data": img_b64,
            "prompt": prompt,
        })

    @mcp.tool()
    async def generate_video(
        prompt: str,
        model: str = "veo",
        duration: int = 8,
        width: int = 1024,
        height: int = 576,
        audio: bool = False,
        save_path: str = "",
    ) -> str:
        """Generate a video from a text prompt (requires POLLINATIONS_API_KEY).

        Args:
            prompt: Video description
            model: Video model (veo, seedance, wan, seedance-pro, seedance-2.0)
            duration: Video duration in seconds (2-15 depending on model)
            width: Width in pixels
            height: Height in pixels
            audio: Include audio (model-dependent)
            save_path: Save directory
        """
        return json.dumps({"success": False, "error": "Video gen not available on free backends. Use Pollinations Pro with API key or HF with credits."})

    @mcp.tool()
    async def list_models() -> str:
        """List available image and video models with pricing info."""
        models = backend_instance.list_models()
        lines = ["Wafle-Imago — modelos disponibles:", ""]
        for m in models:
            cost_str = f"${m['cost']:.3f}" if m["cost"] > 0 else "gratis"
            if m["cost"] == 0 and m["id"] == "anon":
                cost_str = "sin key, sin límite"
            lines.append(f"  {m['id']:20s} │ {m['name']:25s} │ {cost_str:20s} │ {m['type']}")
        lines.append("")
        lines.append(f"Backend activo: {backend_instance.name}")
        return "\n".join(lines)

    @mcp.tool()
    async def get_balance() -> str:
        """Check remaining API balance (if authenticated)."""
        info = {"backend": backend_instance.name, "authenticated": False}

        if backend_instance.name == "cloudflare":
            cf_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
            cf_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
            if cf_token and cf_id:
                info["authenticated"] = True
                info["mode"] = "Cloudflare Workers AI (10k neurons/day free)"
            else:
                info["mode"] = "Necesita CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_API_TOKEN en .env"
                info["signup"] = "https://dash.cloudflare.com/sign-up/workers-and-pages"

        elif backend_instance.name == "nvidia":
            nv_token = os.getenv("NVIDIA_API_KEY", "")
            if nv_token:
                info["authenticated"] = True
                info["mode"] = "NVIDIA NIM (1k req/month free)"
            else:
                info["mode"] = "Necesita NVIDIA_API_KEY en .env"
                info["signup"] = "https://build.nvidia.com"

        elif backend_instance.name == "pollinations":
            token = os.getenv("POLLINATIONS_API_KEY", "")
            if token:
                info["authenticated"] = True
                info["mode"] = "Pollinations Pro (con API key, pago)"
            else:
                info["mode"] = "Pollinations anónimo ya no funciona (HTTP 402). Requiere API key."

        elif backend_instance.name == "hf":
            hf_token = os.getenv("HF_TOKEN", "")
            if hf_token:
                info["authenticated"] = True
                info["mode"] = "HF Inference Providers (créditos pueden estar agotados)"
            else:
                info["mode"] = "Necesita HF_TOKEN en .env"

        return json.dumps(info, ensure_ascii=False)

    return mcp


def main():
    parser = argparse.ArgumentParser(
        prog="wafle-imago",
        description="Wafle-Imago — universal MCP server for AI image generation",
    )
    parser.add_argument("--backend", "-b", default="cloudflare",
                        choices=list(BACKENDS.keys()),
                        help="Backend to use (default: cloudflare — free, 10k neurons/day, no credit card)")
    parser.add_argument("--http", action="store_true",
                        help="Run as HTTP server instead of stdio")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port for HTTP mode (default: 8000)")
    parser.add_argument("--version", "-v", action="version",
                        version=f"Wafle-Imago {__version__}")
    parser.add_argument("--log-dir", default="",
                        help="Directory for audit logs")

    args = parser.parse_args()

    if args.log_dir:
        os.environ["WAFLE_IMAGO_LOG_DIR"] = args.log_dir

    mcp = create_mcp(args.backend)

    if args.http:
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
