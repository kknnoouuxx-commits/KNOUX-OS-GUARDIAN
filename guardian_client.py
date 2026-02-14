from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Protocol, Tuple

from guardian_config import GuardianClientConfig

logger = logging.getLogger(__name__)


class GuardianClientError(Exception):
    pass


class GuardianAuthError(GuardianClientError):
    pass


class GuardianPermissionError(GuardianClientError):
    pass


class GuardianTransientError(GuardianClientError):
    pass


class GuardianProtocolError(GuardianClientError):
    pass


class TokenProvider(Protocol):
    def get_access_token(self) -> str:
        """Return a valid JWT access token (without 'Bearer ')."""


@dataclass(frozen=True)
class GuardianResponse:
    ok: bool
    status_code: int
    data: Optional[Dict[str, Any]]
    raw_text: str
    request_id: Optional[str] = None


def _sleep_with_jitter(base_seconds: float, jitter_seconds: float) -> None:
    time.sleep(max(0.0, base_seconds + random.uniform(0.0, jitter_seconds)))


def retryable(func: Callable[..., GuardianResponse]):
    """Simple retry decorator.

    Retries on GuardianTransientError or when response is not ok with 5xx.
    """

    def wrapper(self: "GuardianClient", *args, **kwargs) -> GuardianResponse:
        policy = self.config.retry
        last_exc: Optional[BaseException] = None

        for attempt in range(1, policy.max_attempts + 1):
            try:
                resp = func(self, *args, **kwargs)

                # Treat 5xx as transient.
                if resp.status_code >= 500:
                    raise GuardianTransientError(f"Server error {resp.status_code}")

                return resp

            except GuardianTransientError as e:
                last_exc = e
                if attempt >= policy.max_attempts:
                    break

                delay = min(policy.max_delay_seconds, policy.base_delay_seconds * (2 ** (attempt - 1)))
                logger.debug(f"retry attempt={attempt} delay={delay}s err={e}")
                _sleep_with_jitter(delay, policy.jitter_seconds)

        raise GuardianTransientError(f"Retries exhausted: {last_exc}")

    return wrapper


def parse_json_response(status_code: int, text: str) -> Dict[str, Any]:
    """Standardized response parser."""
    if not text:
        return {}

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise GuardianProtocolError(f"Response is not valid JSON: {e}")

    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    # For endpoints that return arrays, wrap them.
    return {"items": obj, "_status_code": status_code}


class GuardianClient:
    """API abstraction skeleton.

    - No live API wiring by default (config.enable_http=False)
    - JWT tokens via TokenProvider (no hardcoded tokens)
    - RBAC enforced at client level by checking declared role before calling
    """

    def __init__(
        self,
        config: GuardianClientConfig,
        token_provider: Optional[TokenProvider] = None,
        role_provider: Optional[Callable[[], str]] = None,
    ):
        self.config = config
        self._token_provider = token_provider
        self._role_provider = role_provider

    def _get_role(self) -> Optional[str]:
        if self._role_provider is None:
            return None
        return self._role_provider()

    def _require_role(self, *allowed_roles: str) -> None:
        current_role = self._get_role()
        if current_role is None:
            return
        if current_role not in allowed_roles:
            raise GuardianPermissionError(
                f"Insufficient permissions: role={current_role} allowed={allowed_roles}"
            )

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}

        if self._token_provider is not None:
            token = self._token_provider.get_access_token()
            if not token:
                raise GuardianAuthError("TokenProvider returned empty token")
            headers["Authorization"] = f"Bearer {token}"

        if extra:
            headers.update(extra)

        return headers

    def _http_request(self, method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> GuardianResponse:
        """HTTP placeholder.

        When enable_http=False, this returns a predictable placeholder response.
        When wiring is enabled later, swap internals to use httpx/requests.
        """

        url = self.config.api_base.rstrip("/") + "/" + path.lstrip("/")

        if not self.config.enable_http:
            placeholder = {
                "message": "HTTP wiring is disabled in GuardianClientConfig.enable_http",
                "method": method,
                "url": url,
                "body": json_body or {},
            }
            return GuardianResponse(ok=False, status_code=0, data=placeholder, raw_text=json.dumps(placeholder))

        raise NotImplementedError("HTTP wiring will be added once API layer is finalized")

    @retryable
    def get_module_status(self, module_name: str) -> GuardianResponse:
        self._require_role("admin", "analyst", "viewer")
        resp = self._http_request("GET", f"/modules/{module_name}/status")
        return self._normalize_response(resp)

    @retryable
    def execute_module_immediate(self, module_name: str, parameters: Optional[Dict[str, Any]] = None) -> GuardianResponse:
        self._require_role("admin", "analyst")
        body = {
            "run_mode": "immediate",
            "parameters": parameters or {},
            "priority": "normal",
        }
        resp = self._http_request("POST", f"/modules/{module_name}/execute", json_body=body)
        return self._normalize_response(resp)

    @retryable
    def execute_module_async(self, module_name: str, parameters: Optional[Dict[str, Any]] = None) -> GuardianResponse:
        self._require_role("admin", "analyst")
        body = {
            "run_mode": "async",
            "parameters": parameters or {},
            "priority": "normal",
        }
        resp = self._http_request("POST", f"/modules/{module_name}/execute", json_body=body)
        return self._normalize_response(resp)

    @retryable
    def get_async_task_status(self, run_id: str) -> GuardianResponse:
        self._require_role("admin", "analyst")
        resp = self._http_request("GET", f"/async/tasks/{run_id}")
        return self._normalize_response(resp)

    @retryable
    def get_execution_result(self, module_name: str, run_id: str) -> GuardianResponse:
        self._require_role("admin", "analyst", "viewer")
        resp = self._http_request("GET", f"/modules/{module_name}/runs/{run_id}")
        return self._normalize_response(resp)

    def audit_correlation_placeholder(self, run_id: str) -> Dict[str, Any]:
        """Placeholder for audit correlation.

        Once the audit endpoints are confirmed, this should query /audit/logs?...
        """
        return {
            "run_id": run_id,
            "status": "placeholder",
            "note": "Audit correlation wiring will be added once API is finalized",
        }

    def _normalize_response(self, resp: GuardianResponse) -> GuardianResponse:
        """Standardize response parsing and raise on auth/permission errors."""
        if resp.data is None and resp.raw_text:
            try:
                data = parse_json_response(resp.status_code, resp.raw_text)
            except GuardianProtocolError:
                data = None
            resp = GuardianResponse(
                ok=resp.ok,
                status_code=resp.status_code,
                data=data,
                raw_text=resp.raw_text,
                request_id=resp.request_id,
            )

        # Placeholder errors:
        if resp.status_code in (401,):
            raise GuardianAuthError("Unauthorized")
        if resp.status_code in (403,):
            raise GuardianPermissionError("Forbidden")

        return resp
