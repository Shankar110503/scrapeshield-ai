from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests


class BrightDataClient:
    """Bright Data client with safe asynchronous dataset polling."""

    def __init__(
        self,
        token: Optional[str] = None,
        collector: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.token = token or os.getenv("BRIGHT_DATA_API_TOKEN", "")
        self.collector = collector or os.getenv("BRIGHT_DATA_COLLECTOR_ID", "")
        self.base_url = (
            base_url or os.getenv(
                "BRIGHT_DATA_BASE_URL",
                "https://api.brightdata.com",
            )
        ).rstrip("/")

        if not self.token:
            raise ValueError("BRIGHT_DATA_API_TOKEN is missing.")
        if not self.collector:
            raise ValueError("BRIGHT_DATA_COLLECTOR_ID is missing.")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _body(response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _still_collecting(body: Any) -> bool:
        if not isinstance(body, dict):
            return False

        status = str(body.get("status", "")).lower()
        message = str(body.get("message", "")).lower()

        statuses = {
            "collecting", "running", "pending", "processing",
            "in_progress", "in progress", "queued"
        }

        if status in statuses:
            return True

        phrases = (
            "not finished",
            "not ready",
            "still collecting",
            "in progress",
            "job is not finished",
            "processing",
        )
        return any(p in message for p in phrases)

    @staticmethod
    def _collection_id(body: Any) -> str:
        if isinstance(body, str) and body.strip():
            return body.strip()

        if not isinstance(body, dict):
            raise RuntimeError(f"Unexpected Bright Data trigger response: {body}")

        keys = ("collection_id", "collectionId", "id", "job_id", "jobId")

        for key in keys:
            if body.get(key):
                return str(body[key])

        for parent in ("result", "data", "collection"):
            nested = body.get(parent)
            if isinstance(nested, dict):
                for key in keys:
                    if nested.get(key):
                        return str(nested[key])

        raise RuntimeError(
            f"Bright Data trigger response has no collection ID: {body}"
        )

    def trigger(self, inputs: List[Dict[str, Any]]) -> str:
        response = requests.post(
            f"{self.base_url}/dca/trigger",
            params={"collector": self.collector},
            headers=self.headers,
            json=inputs,
            timeout=60,
        )

        body = self._body(response)

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data trigger error {response.status_code}: {body}"
            )

        return self._collection_id(body)

    @staticmethod
    def _records(body: Any) -> Optional[List[Dict[str, Any]]]:
        if isinstance(body, list):
            return body

        if not isinstance(body, dict):
            return None

        if BrightDataClient._still_collecting(body):
            return None

        for key in ("results", "records", "data"):
            value = body.get(key)
            if isinstance(value, list):
                return value

        result = body.get("result")
        if isinstance(result, list):
            return result

        if isinstance(result, dict):
            for key in ("results", "records", "data"):
                value = result.get(key)
                if isinstance(value, list):
                    return value

        return None

    def dataset(self, collection_id: str) -> Optional[List[Dict[str, Any]]]:
        response = requests.get(
            f"{self.base_url}/dca/get_result",
            params={"collection_id": collection_id},
            headers=self.headers,
            timeout=60,
        )

        body = self._body(response)

        # Async collection is still running.
        if response.status_code in (202, 204):
            return None

        if response.status_code >= 400:
            if self._still_collecting(body):
                return None
            raise RuntimeError(
                f"Bright Data dataset error {response.status_code}: {body}"
            )

        records = self._records(body)
        if records is not None:
            return records

        if self._still_collecting(body):
            return None

        raise RuntimeError(
            f"Bright Data returned unexpected dataset response: {body}"
        )

    def collect(
        self,
        inputs: List[Dict[str, Any]],
        timeout: int = 600,
        poll_interval: int = 5,
    ) -> Tuple[List[Dict[str, Any]], str]:
        collection_id = self.trigger(inputs)
        started = time.monotonic()

        while time.monotonic() - started < timeout:
            data = self.dataset(collection_id)

            if isinstance(data, list):
                return data, collection_id

            remaining = max(
                0,
                timeout - int(time.monotonic() - started),
            )

            if remaining <= 0:
                break

            time.sleep(min(poll_interval, remaining))

        raise RuntimeError(
            "Timed out waiting for Bright Data dataset. "
            f"Collection ID: {collection_id}"
        )

    def self_heal(self, prompt: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/dca/collectors/"
            f"{self.collector}/refactor_template",
            headers=self.headers,
            json={"prompt": prompt},
            timeout=60,
        )

        result = self._body(response)

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data Self-Healing error "
                f"{response.status_code}: {result}"
            )

        return result if isinstance(result, dict) else {"result": result}

    def self_heal_progress(self) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/dca/collectors/"
            f"{self.collector}/refactor_template/progress",
            headers=self.headers,
            timeout=60,
        )

        result = self._body(response)

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data Self-Healing progress error "
                f"{response.status_code}: {result}"
            )

        return result if isinstance(result, dict) else {"result": result}
