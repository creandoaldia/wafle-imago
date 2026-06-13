"""Pollinations backend — free, no-auth image generation."""

import time
import urllib.error
import urllib.request
import urllib.parse
import os
from pathlib import Path
from typing import Any

from .base import BaseBackend, GenerationResult, BACKENDS


ANON_BASE = "https://pollinations.ai/p/"
ANON_FALLBACK = "https://image.pollinations.ai/prompt/"
PRO_BASE = "https://gen.pollinations.ai"


class PollinationsBackend(BaseBackend):
    name = "pollinations"
    priority = 0

    def _fetch_anon(self, prompt: str, retries: int = 2, url_base: str = "") -> bytes:
        base = url_base or ANON_BASE
        url = base + urllib.parse.quote(prompt)
        last_err = ""
        for attempt in range(1, retries + 2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "WafleImago/0.1"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    ct = (r.headers.get("Content-Type") or "").lower()
                    data = r.read()
                if ct and "text/html" in ct:
                    last_err = "Pollinations returned HTML instead of image (rate limit / captcha)"
                    time.sleep(1.5)
                    continue
                if data[:4] == b"\x89PNG" or data[:2] in (b"\xff\xd8", b"BM"):
                    return data
                html_indicators = [b"<!DOCTYPE html", b"<html", b"<script"]
                if any(ind in data[:500].lower() for ind in [b"<!doctype html", b"<html", b"<script"]):
                    last_err = "Response is HTML, not an image (Pollinations may be rate-limiting)"
                    time.sleep(1.5)
                    continue
                return data
            except urllib.error.HTTPError as e:
                last_err = f"HTTP {e.code}: {e.reason[:100]}"
                time.sleep(2 ** attempt)
            except Exception as e:
                last_err = str(e)[:200]
                time.sleep(2 ** attempt)
        raise RuntimeError(f"Anonymous Pollinations failed after {retries + 1} attempts: {last_err}")

    def _fetch_pro(self, prompt: str, model: str, **kwargs: Any) -> bytes:
        token = self._get_token()
        if not token:
            raise ValueError("POLLINATIONS_API_KEY required for pro mode")

        params = {"model": model}
        if w := kwargs.get("width"): params["width"] = str(w)
        if h := kwargs.get("height"): params["height"] = str(h)
        if kwargs.get("safe", True): params["safe"] = "true"
        if kwargs.get("quality"): params["quality"] = kwargs["quality"]
        if kwargs.get("transparent"): params["transparent"] = "true"

        is_video = model in ("veo", "seedance", "wan", "seedance-pro", "seedance-2.0")
        if is_video:
            if d := kwargs.get("duration"): params["duration"] = str(d)
            if kwargs.get("audio"): params["audio"] = "true"

        endpoint = "video" if is_video else "image"
        qs = urllib.parse.urlencode(params)
        url = f"{PRO_BASE}/{endpoint}/{urllib.parse.quote(prompt)}?{qs}"

        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "WafleImago/0.1",
        })
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()

    def _get_token(self) -> str | None:
        if t := os.getenv("POLLINATIONS_API_KEY"):
            return t
        env_path = Path(r"C:\web-ai-lab\.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("POLLINATIONS_API_KEY="):
                    return line.split("=", 1)[1].strip()
        return None

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        model = kwargs.get("model", "")
        is_video = model in ("veo", "seedance", "wan", "seedance-pro", "seedance-2.0")
        token = self._get_token()
        t0 = time.time()

        try:
            if token and model:
                data = self._fetch_pro(prompt, model, **kwargs)
            else:
                try:
                    data = self._fetch_anon(prompt)
                except Exception:
                    if ANON_FALLBACK:
                        data = self._fetch_anon(prompt, url_base=ANON_FALLBACK)

            elapsed = round(time.time() - t0, 1)
            if data[:4] == b"\x89PNG":
                fmt = "image/png"
            elif data[:2] in (b"\xff\xd8",):
                fmt = "image/jpeg"
            elif data[:2] == b"BM":
                fmt = "image/bmp"
            else:
                fmt = "image/png"
            return GenerationResult(
                success=True, data=data, format=fmt,
                time_seconds=elapsed, model=model or "zimage", attempts=1,
            )
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            return GenerationResult(
                success=False, error=str(e)[:300],
                time_seconds=elapsed, model=model or "zimage",
            )

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": "anon", "name": "Anonymous (no key)", "cost": 0, "type": "image"},
            {"id": "flux", "name": "FLUX", "cost": 0.005, "type": "image"},
            {"id": "gptimage", "name": "GPT Image", "cost": 0.05, "type": "image"},
            {"id": "seedream", "name": "Seedream 5.0", "cost": 0.04, "type": "image"},
            {"id": "zimage", "name": "zimage (default)", "cost": 0.002, "type": "image"},
            {"id": "veo", "name": "Veo 3", "cost": 0.50, "type": "video"},
            {"id": "seedance", "name": "Seedance", "cost": 0.20, "type": "video"},
            {"id": "wan", "name": "Wan 2.2", "cost": 0.10, "type": "video"},
        ]


BACKENDS["pollinations"] = PollinationsBackend
