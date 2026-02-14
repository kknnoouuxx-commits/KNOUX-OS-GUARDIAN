from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 5.0
    jitter_seconds: float = 0.2


@dataclass(frozen=True)
class GuardianClientConfig:
    base_url: str = "http://localhost:8000"
    api_prefix: str = "/api/v1"

    timeout_seconds: float = 10.0
    retry: RetryPolicy = RetryPolicy()

    # No hardcoded tokens; provide them at runtime via a token provider.
    # HTTP wiring can be toggled when the API is finalized.
    enable_http: bool = False

    # Logging
    log_level: str = "INFO"

    @property
    def api_base(self) -> str:
        return self.base_url.rstrip("/") + self.api_prefix

    @staticmethod
    def from_env() -> "GuardianClientConfig":
        base_url = os.getenv("GUARDIAN_BASE_URL", "http://localhost:8000")
        api_prefix = os.getenv("GUARDIAN_API_PREFIX", "/api/v1")
        timeout_seconds = float(os.getenv("GUARDIAN_TIMEOUT_SECONDS", "10"))

        max_attempts = int(os.getenv("GUARDIAN_RETRY_MAX_ATTEMPTS", "3"))
        base_delay = float(os.getenv("GUARDIAN_RETRY_BASE_DELAY_SECONDS", "0.5"))
        max_delay = float(os.getenv("GUARDIAN_RETRY_MAX_DELAY_SECONDS", "5"))
        jitter = float(os.getenv("GUARDIAN_RETRY_JITTER_SECONDS", "0.2"))

        enable_http = os.getenv("GUARDIAN_ENABLE_HTTP", "false").lower() in ("1", "true", "yes")
        log_level = os.getenv("GUARDIAN_LOG_LEVEL", "INFO").upper()

        return GuardianClientConfig(
            base_url=base_url,
            api_prefix=api_prefix,
            timeout_seconds=timeout_seconds,
            retry=RetryPolicy(
                max_attempts=max_attempts,
                base_delay_seconds=base_delay,
                max_delay_seconds=max_delay,
                jitter_seconds=jitter,
            ),
            enable_http=enable_http,
            log_level=log_level,
        )


def configure_structured_logging(level: Optional[str] = None) -> None:
    log_level = (level or os.getenv("GUARDIAN_LOG_LEVEL", "INFO")).upper()

    # Keep it dependency-free: JSON-ish key=value pairs for easy ingestion.
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=(
            "%(asctime)s level=%(levelname)s logger=%(name)s "
            "msg=%(message)s"
        ),
    )
