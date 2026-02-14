from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from guardian_client import GuardianClient, GuardianResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionHandle:
    module_name: str
    run_id: str
    run_mode: str


@dataclass(frozen=True)
class PollingPolicy:
    poll_interval_seconds: float = 1.0
    max_wait_seconds: float = 60.0


class ExecutionManager:
    """Async orchestration + polling logic placeholder.

    Responsibilities:
    - handle 202/async-style scheduling
    - poll task status endpoint
    - fetch execution result when completed
    - track execution IDs for audit correlation

    Note: No live wiring assumptions; uses GuardianClient which can be HTTP-disabled.
    """

    def __init__(self, client: GuardianClient, polling: Optional[PollingPolicy] = None):
        self.client = client
        self.polling = polling or PollingPolicy()

    def start_immediate(self, module_name: str, parameters: Optional[Dict[str, Any]] = None) -> Tuple[ExecutionHandle, GuardianResponse]:
        resp = self.client.execute_module_immediate(module_name, parameters=parameters)
        run_id = self._extract_run_id(resp, fallback_prefix="IMMEDIATE")
        handle = ExecutionHandle(module_name=module_name, run_id=run_id, run_mode="immediate")
        return handle, resp

    def start_async(self, module_name: str, parameters: Optional[Dict[str, Any]] = None) -> Tuple[ExecutionHandle, GuardianResponse]:
        resp = self.client.execute_module_async(module_name, parameters=parameters)
        run_id = self._extract_run_id(resp, fallback_prefix="ASYNC")
        handle = ExecutionHandle(module_name=module_name, run_id=run_id, run_mode="async")
        return handle, resp

    def wait_for_completion(self, handle: ExecutionHandle) -> GuardianResponse:
        """Polling structure only.

        - polls /async/tasks/{run_id} until completed/failed or timeout
        - then calls /modules/{module}/runs/{run_id} to return final result
        """

        deadline = time.time() + self.polling.max_wait_seconds

        while time.time() < deadline:
            status_resp = self.client.get_async_task_status(handle.run_id)
            status = self._safe_get(status_resp.data, "status")

            logger.info(
                "poll run_id=%s module=%s status=%s",
                handle.run_id,
                handle.module_name,
                status,
            )

            if status in ("completed", "failed"):
                break

            time.sleep(self.polling.poll_interval_seconds)

        # Placeholder: fetch result (even if timeout, downstream will decide)
        return self.client.get_execution_result(handle.module_name, handle.run_id)

    def audit_correlation(self, handle: ExecutionHandle) -> Dict[str, Any]:
        """Placeholder design for audit correlation."""
        return self.client.audit_correlation_placeholder(handle.run_id)

    def _extract_run_id(self, resp: GuardianResponse, fallback_prefix: str) -> str:
        if resp.data and isinstance(resp.data, dict):
            run_id = resp.data.get("run_id") or resp.data.get("execution_id") or resp.data.get("request_id")
            if isinstance(run_id, str) and run_id:
                return run_id

        # fallback stable identifier for logs/testing when HTTP is disabled
        return f"{fallback_prefix}_{int(time.time())}"

    @staticmethod
    def _safe_get(d: Optional[Dict[str, Any]], key: str) -> Optional[Any]:
        if not d or not isinstance(d, dict):
            return None
        return d.get(key)
