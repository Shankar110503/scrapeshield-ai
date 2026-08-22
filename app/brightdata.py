from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests


class BrightDataClient:
    """
    Bright Data Scraper Studio client.

    Flow:
        POST /dca/trigger
            ↓
        collection_id
            ↓
        GET /dca/dataset?id=<collection_id>
            ↓
        structured records
    """

    def __init__(
        self,
        token: Optional[str] = None,
        collector: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:

        self.token = token or os.getenv(
            "BRIGHT_DATA_API_TOKEN", ""
        )

        self.collector = collector or os.getenv(
            "BRIGHT_DATA_COLLECTOR_ID", ""
        )

        self.base_url = (
            base_url
            or os.getenv(
                "BRIGHT_DATA_BASE_URL",
                "https://api.brightdata.com",
            )
        ).rstrip("/")

        if not self.token:
            raise ValueError(
                "BRIGHT_DATA_API_TOKEN is missing."
            )

        if not self.collector:
            raise ValueError(
                "BRIGHT_DATA_COLLECTOR_ID is missing."
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _body(response: requests.Response) -> Any:
        """
        Safely decode a Bright Data response.
        """

        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _still_collecting(body: Any) -> bool:
        """
        Detect whether Bright Data is still processing
        the collection.
        """

        if not isinstance(body, dict):
            return False

        status = str(
            body.get("status", "")
        ).strip().lower()

        message = str(
            body.get("message", "")
        ).strip().lower()

        collecting_statuses = {
            "collecting",
            "running",
            "pending",
            "processing",
            "in_progress",
            "in progress",
            "queued",
            "started",
        }

        if status in collecting_statuses:
            return True

        phrases = (
            "not finished",
            "not ready",
            "still collecting",
            "in progress",
            "job is not finished",
            "processing",
            "please wait",
            "collection is running",
        )

        return any(
            phrase in message
            for phrase in phrases
        )

    @staticmethod
    def _collection_id(body: Any) -> str:
        """
        Extract collection_id from Bright Data trigger response.
        """

        if isinstance(body, str) and body.strip():
            return body.strip()

        if not isinstance(body, dict):
            raise RuntimeError(
                "Unexpected Bright Data trigger response: "
                f"{body}"
            )

        possible_keys = (
            "collection_id",
            "collectionId",
            "id",
            "job_id",
            "jobId",
        )

        # Direct keys
        for key in possible_keys:
            value = body.get(key)

            if value:
                return str(value)

        # Nested objects
        for parent in (
            "result",
            "data",
            "collection",
        ):

            nested = body.get(parent)

            if isinstance(nested, dict):

                for key in possible_keys:

                    value = nested.get(key)

                    if value:
                        return str(value)

        raise RuntimeError(
            "Bright Data trigger response does not "
            f"contain a collection ID:\n{body}"
        )

    # ---------------------------------------------------------
    # Trigger collector
    # ---------------------------------------------------------

    def trigger(
        self,
        inputs: List[Dict[str, Any]],
    ) -> str:

        response = requests.post(
            f"{self.base_url}/dca/trigger",
            params={
                "collector": self.collector,
                "queue_next": "1",
            },
            headers=self.headers,
            json=inputs,
            timeout=60,
        )

        body = self._body(response)

        if response.status_code >= 400:

            raise RuntimeError(
                "Bright Data trigger error "
                f"{response.status_code}: {body}"
            )

        return self._collection_id(body)

    # ---------------------------------------------------------
    # Extract records
    # ---------------------------------------------------------

    @staticmethod
    def _records(
        body: Any,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Convert all common Bright Data response formats
        into a list of dictionaries.
        """

        # ---------------------------------------------
        # Standard documented response:
        #
        # [
        #   {...},
        #   {...}
        # ]
        # ---------------------------------------------

        if isinstance(body, list):

            return [
                item
                for item in body
                if isinstance(item, dict)
            ]

        # Nothing useful
        if body is None:
            return None

        if not isinstance(body, dict):
            return None

        # ---------------------------------------------
        # Still processing?
        # ---------------------------------------------

        if BrightDataClient._still_collecting(body):
            return None

        # ---------------------------------------------
        # Common wrappers
        # ---------------------------------------------

        for key in (
            "results",
            "records",
            "data",
            "items",
            "rows",
        ):

            value = body.get(key)

            if isinstance(value, list):

                return [
                    item
                    for item in value
                    if isinstance(item, dict)
                ]

        # ---------------------------------------------
        # Nested result
        # ---------------------------------------------

        result = body.get("result")

        if isinstance(result, list):

            return [
                item
                for item in result
                if isinstance(item, dict)
            ]

        if isinstance(result, dict):

            for key in (
                "results",
                "records",
                "data",
                "items",
                "rows",
            ):

                value = result.get(key)

                if isinstance(value, list):

                    return [
                        item
                        for item in value
                        if isinstance(item, dict)
                    ]

        # ---------------------------------------------
        # Single-record response
        #
        # This is important for your current error:
        #
        # {
        #   "url": "...",
        #   "input": {
        #       "url": "..."
        #   }
        # }
        #
        # Accept it instead of throwing
        # "unexpected dataset response".
        # ---------------------------------------------

        extraction_keys = {
            "product_name",
            "product",
            "name",
            "title",
            "price",
            "stock",
            "availability",
            "image",
            "description",
            "url",
        }

        if any(
            key in body
            for key in extraction_keys
        ):

            return [dict(body)]

        # ---------------------------------------------
        # If Bright Data returned only metadata/input,
        # still return it as one record so the dashboard
        # can detect missing fields instead of crashing.
        # ---------------------------------------------

        if (
            "input" in body
            or "url" in body
        ):

            return [dict(body)]

        return None

    # ---------------------------------------------------------
    # Dataset
    # ---------------------------------------------------------

    def dataset(
        self,
        collection_id: str,
    ) -> Optional[List[Dict[str, Any]]]:

        response = requests.get(
            f"{self.base_url}/dca/dataset",
            params={
                "id": collection_id,
            },
            headers=self.headers,
            timeout=60,
        )

        body = self._body(response)

        # ---------------------------------------------
        # Collection is still running
        # ---------------------------------------------

        if response.status_code in (
            202,
            204,
        ):

            return None

        # ---------------------------------------------
        # API error
        # ---------------------------------------------

        if response.status_code >= 400:

            if self._still_collecting(body):
                return None

            raise RuntimeError(
                "Bright Data dataset error "
                f"{response.status_code}: {body}"
            )

        # ---------------------------------------------
        # Extract records
        # ---------------------------------------------

        records = self._records(body)

        if records is not None:
            return records

        if self._still_collecting(body):
            return None

        raise RuntimeError(
            "Bright Data returned an unsupported "
            f"dataset response:\n{body}"
        )

    # ---------------------------------------------------------
    # Complete collection
    # ---------------------------------------------------------

    def collect(
        self,
        inputs: List[Dict[str, Any]],
        timeout: int = 600,
        poll_interval: int = 5,
    ) -> Tuple[List[Dict[str, Any]], str]:

        collection_id = self.trigger(inputs)

        started = time.monotonic()

        while (
            time.monotonic() - started
            < timeout
        ):

            data = self.dataset(
                collection_id
            )

            if isinstance(data, list):

                return (
                    data,
                    collection_id,
                )

            elapsed = int(
                time.monotonic() - started
            )

            remaining = max(
                0,
                timeout - elapsed,
            )

            if remaining <= 0:
                break

            time.sleep(
                min(
                    poll_interval,
                    remaining,
                )
            )

        raise RuntimeError(
            "Timed out waiting for Bright Data "
            "dataset.\n"
            f"Collection ID: {collection_id}"
        )

    # ---------------------------------------------------------
    # Bright Data Self-Healing
    # ---------------------------------------------------------

    def self_heal(
        self,
        prompt: str,
    ) -> Dict[str, Any]:

        response = requests.post(
            (
                f"{self.base_url}"
                f"/dca/collectors/"
                f"{self.collector}"
                f"/refactor_template"
            ),
            headers=self.headers,
            json={
                "prompt": prompt,
            },
            timeout=60,
        )

        result = self._body(response)

        if response.status_code >= 400:

            raise RuntimeError(
                "Bright Data Self-Healing error "
                f"{response.status_code}: {result}"
            )

        if isinstance(result, dict):
            return result

        return {
            "result": result
            }
