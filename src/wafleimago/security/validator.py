"""Prompt validation and security checks."""

import re
import time
from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    risk: str = "none"
    reason: str = ""
    sanitized_prompt: str = ""


BLOCKED_PATTERNS = [
    (r"(?i)\bnsfw\b", "NSFW content blocked"),
    (r"(?i)\bexplicit\b", "Explicit content blocked"),
    (r"(?i)\bnude\b", "NSFW content blocked"),
    (r"(?i)\bporn\b", "NSFW content blocked"),
    (r"(?i)\bsex(?:ual)?\b", "Explicit content blocked"),
    (r"(?i)\bgore\b", "Violent content blocked"),
    (r"(?i)\bviolence\b", "Violent content blocked"),
    (r"(?i)\b(?:system|ignore|forget)\s+(?:prompt|instruction|previous)", "Prompt injection blocked"),
    (r"(?i)\bignore\s+(?:all\s+)?(?:previous|above|instructions)", "Prompt injection blocked"),
    (r"(?i)reveal\s+(?:your\s+)?(?:prompt|system|secret|key|token)", "Prompt injection blocked"),
]


def validate_prompt(prompt: str, strict: bool = True) -> ValidationResult:
    if not prompt or not prompt.strip():
        return ValidationResult(valid=False, risk="empty", reason="Prompt vacío")
    if len(prompt) > 5000:
        return ValidationResult(valid=False, risk="too_long", reason="Prompt excede 5000 caracteres")
    if strict:
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, prompt):
                sanitized = re.sub(pattern, "[REDACTED]", prompt, flags=re.IGNORECASE)
                return ValidationResult(valid=False, risk="blocked", reason=reason, sanitized_prompt=sanitized)
    return ValidationResult(valid=True, risk="none", sanitized_prompt=prompt)


class RateLimiter:
    def __init__(self, max_per_minute: int = 30, max_per_hour: int = 500):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self._minute: list[float] = []
        self._hour: list[float] = []

    def check(self) -> tuple[bool, str]:
        now = time.time()
        self._minute = [t for t in self._minute if now - t < 60]
        self._hour = [t for t in self._hour if now - t < 3600]
        if len(self._minute) >= self.max_per_minute:
            return False, f"Rate limit: {self.max_per_minute}/minuto"
        if len(self._hour) >= self.max_per_hour:
            return False, f"Rate limit: {self.max_per_hour}/hora"
        self._minute.append(now)
        self._hour.append(now)
        return True, ""

    def reset(self):
        self._minute.clear()
        self._hour.clear()
