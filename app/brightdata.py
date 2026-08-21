"""
Bright Data client for ScrapeShield AI.

Handles:
- collector trigger
- asynchronous dataset polling
- "collecting / job not finished" responses
- self-healing/refactor requests
- self-healing progress
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests


BASE_URL = os.getenv("BRIGHT_DATA_BASE_URL", "https://api.brightdata.com").rstrip("/")


class BrightDataClient:
    def __init__(
        self,
        token: Optional[str] = None,
        collector: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.token = token or os.getenv("BRIGHT_DATA_API_TOKEN", "")
        self.collector = collector or os.getenv("BRIGHT_DATA_COLLECTOR_ID", "")
        self.base_url = (base_url or BASE_URL).rstrip("/")

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
    def _json_or_text(response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _extract_collection_id(body: Any) -> str:
        if isinstance(body, str) and body.strip():
            return body.strip()

        if not isinstance(body, dict):
            raise RuntimeError(f"Unexpected trigger response: {body}")

        for key in (
            "collection_id",
            "collectionId",
            "id",
            "job_id",
            "jobId",
        ):
            value = body.get(key)
            if value:
                return str(value)

        # Some responses nest the ID.
        for parent in ("result", "data", "collection"):
            nested = body.get(parent)
            if isinstance(nested, dict):
                for key in ("collection_id", "collectionId", "id", "job_id", "jobId"):
                    value = nested.get(key)
                    if value:
                        return str(value)

        raise RuntimeError(f"Bright Data trigger response has no collection ID: {body}")

    def trigger(self, inputs: List[Dict[str, Any]]) -> str:
        url = f"{self.base_url}/dca/trigger"
        params = {"collector": self.collector}

        response = requests.post(
            url,
            params=params,
            headers=self.headers,
            json=inputs,
            timeout=60,
        )

        body = self._json_or_text(response)

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data trigger error {response.status_code}: {body}"
            )

        return self._extract_collection_id(body)

    @staticmethod
    def _is_still_collecting(body: Any) -> bool:
        if not isinstance(body, dict):
            return False

        status = str(body.get("status", "")).lower()
        message = str(body.get("message", "")).lower()

        waiting_statuses = {
            "collecting",
            "running",
            "pending",
            "processing",
            "in_progress",
            "in progress",
            "queued",
        }

        if status in waiting_statuses:
            return True

        waiting_words = (
            "not finished",
            "not ready",
            "still collecting",
            "in progress",
            "job is not finished",
            "processing",
        )

        return any(word in message for word in waiting_words)

    @staticmethod
    def _extract_records(body: Any) -> Optional[List[Dict[str, Any]]]:
        # Direct list response.
        if isinstance(body, list):
            return body

        if not isinstance(body, dict):
            return None

        # A still-running collection is NOT an error.
        if BrightDataClient._is_still_collecting(body):
            return None

        # Common result containers.
        for key in ("results", "records", "data"):
            value = body.get(key)
            if isinstance(value, list):
                return value

        # Sometimes the result itself is nested.
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
        url = f"{self.base_url}/dca/get_result"
        params = {"collection_id": collection_id}

        response = requests.get(
            url,
            params=params,
            headers=self.headers,
            timeout=60,
        )

        body = self._json_or_text(response)

        # 202/204 can mean the asynchronous job is not ready.
        if response.status_code in (202, 204):
            return None

        if response.status_code >= 400:
            # Some Bright Data responses put "Job is not finished"
            # inside a 4xx response. Treat that as a polling state.
            if self._is_still_collecting(body):
                return None

            raise RuntimeError(
                f"Bright Data dataset error {response.status_code}: {body}"
            )

        records = self._extract_records(body)

        if records is not None:
            return records

        # Do not crash merely because Bright Data says the job is still running.
        if self._is_still_collecting(body):
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
        """
        Trigger the collector and wait until the dataset is ready.

        The important fix is that a response such as:
        {"status": "collecting", "message": "Job is not finished"}
        is treated as a normal polling state, not a fatal exception.
        """
        collection_id = self.trigger(inputs)
        started = time.monotonic()

        while time.monotonic() - started < timeout:
            data = self.dataset(collection_id)

            if isinstance(data, list):
                return data, collection_id

            elapsed = int(time.monotonic() - started)
            remaining = max(0, timeout - elapsed)

            if remaining <= 0:
                break

            time.sleep(min(poll_interval, remaining))

        raise RuntimeError(
            "Timed out waiting for Bright Data dataset. "
            f"Collection ID: {collection_id}"
        )

    def self_heal(self, prompt: str) -> Dict[str, Any]:
        url = (
            f"{self.base_url}/dca/collectors/"
            f"{self.collector}/refactor_template"
        )

        response = requests.post(
            url,
            headers=self.headers,
            json={"prompt": prompt},
            timeout=60,
        )

        result = self._json_or_text(response)

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data Self-Healing error "
                f"{response.status_code}: {result}"
            )

        if isinstance(result, dict):
            return result

        return {"result": result}

    def self_heal_progress(self) -> Dict[str, Any]:
        url = (
            f"{self.base_url}/dca/collectors/"
            f"{self.collector}/refactor_template/progress"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=60,
        )

        result = self._json_or_text(response)

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data Self-Healing progress error "
                f"{response.status_code}: {result}"
            )

        if isinstance(result, dict):
            return result

        return {"result": result}
