"""Audit logging for image generation."""

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("wafle-imago")


class AuditLogger:
    def __init__(self, log_dir: str | None = None):
        self.log_dir = log_dir
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)

    def log(self, event: str, metadata: dict[str, Any] | None = None) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "event": event,
        }
        if metadata:
            entry.update(metadata)
        logger.info(json.dumps(entry))
        if self.log_dir:
            path = Path(self.log_dir) / f"wafle-imago-{time.strftime('%Y-%m-%d')}.jsonl"
            with open(path, "a") as f:
                f.write(json.dumps(entry) + "\n")

    def generation(self, model: str, prompt: str, success: bool,
                   time_s: float, backend: str, size_bytes: int = 0,
                   risk: str = "none") -> None:
        self.log("generation", {
            "backend": backend, "model": model, "prompt": prompt[:120],
            "success": success, "time_seconds": time_s,
            "size_bytes": size_bytes, "risk": risk,
        })

    def error(self, backend: str, error: str, prompt: str = "") -> None:
        self.log("error", {
            "backend": backend, "error": error[:200], "prompt": prompt[:120],
        })
