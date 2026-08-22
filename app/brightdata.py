import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests


BASE_URL = "https://api.brightdata.com"


class BrightDataClient:
    """Bright Data Scraper Studio client."""

    def __init__(self) -> None:

        self.token = os.getenv(
            "BRIGHT_DATA_API_TOKEN"
        )

        self.collector = os.getenv(
            "BRIGHT_DATA_COLLECTOR_ID"
        )

        if not self.token:
            raise RuntimeError(
                "BRIGHT_DATA_API_TOKEN is not set."
            )

        if not self.collector:
            raise RuntimeError(
                "BRIGHT_DATA_COLLECTOR_ID is not set."
            )

    @property
    def headers(self) -> Dict[str, str]:

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # --------------------------------------------------
    # TRIGGER
    # --------------------------------------------------

    def trigger(
        self,
        inputs: List[Dict[str, Any]],
    ) -> str:

        response = requests.post(
            f"{BASE_URL}/dca/trigger",
            params={
                "collector": self.collector,
                "queue_next": 1,
            },
            headers=self.headers,
            json=inputs,
            timeout=60,
        )

        try:
            result = response.json()
        except ValueError:
            result = response.text

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data trigger error "
                f"{response.status_code}: {result}"
            )

        if not isinstance(result, dict):
            raise RuntimeError(
                "Unexpected Bright Data trigger response: "
                f"{result}"
            )

        collection_id = result.get(
            "collection_id"
        )

        if not collection_id:
            raise RuntimeError(
                "Bright Data did not return "
                f"collection_id: {result}"
            )

        return str(collection_id)

    # --------------------------------------------------
    # NORMALIZE ONE RECORD
    # --------------------------------------------------

    @staticmethod
    def normalize_record(
        record: Dict[str, Any]
    ) -> Dict[str, Any]:

        result = dict(record)

        # Product name aliases
        if not result.get("product_name"):

            for key in (
                "product_name",
                "Product Name",
                "product",
                "Product",
                "name",
                "Name",
                "title",
                "Title",
            ):

                value = result.get(key)

                if value not in (
                    None,
                    "",
                ):

                    result["product_name"] = value
                    break

        # Price aliases
        if not result.get("price"):

            for key in (
                "price",
                "Price",
                "product_price",
                "Product Price",
            ):

                value = result.get(key)

                if value not in (
                    None,
                    "",
                ):

                    result["price"] = value
                    break

        # Stock aliases
        if not result.get("stock"):

            for key in (
                "stock",
                "Stock",
                "availability",
                "Availability",
                "in_stock",
                "In Stock",
            ):

                value = result.get(key)

                if value not in (
                    None,
                    "",
                ):

                    result["stock"] = value
                    break

        return result

    # --------------------------------------------------
    # PARSE DATASET
    # --------------------------------------------------

    @classmethod
    def parse_dataset(
        cls,
        body: Any,
    ) -> Optional[List[Dict[str, Any]]]:

        # ----------------------------------------------
        # Bright Data ready response
        #
        # [
        #   {...},
        #   {...}
        # ]
        # ----------------------------------------------

        if isinstance(body, list):

            records = []

            for item in body:

                if isinstance(item, dict):

                    records.append(
                        cls.normalize_record(item)
                    )

            return records

        # ----------------------------------------------
        # Response must be dictionary from here
        # ----------------------------------------------

        if not isinstance(body, dict):

            return None

        status = str(
            body.get("status", "")
        ).strip().lower()

        # ----------------------------------------------
        # Bright Data still processing
        # ----------------------------------------------

        pending_statuses = {
            "building",
            "running",
            "pending",
            "starting",
            "queued",
            "processing",
            "in_progress",
            "in progress",
        }

        if status in pending_statuses:
            return None

        # ----------------------------------------------
        # Wrapped list responses
        # ----------------------------------------------

        for key in (
            "data",
            "results",
            "records",
            "items",
            "rows",
        ):

            value = body.get(key)

            if isinstance(value, list):

                records = []

                for item in value:

                    if isinstance(item, dict):

                        records.append(
                            cls.normalize_record(item)
                        )

                return records

        # ----------------------------------------------
        # Nested result
        # ----------------------------------------------

        result = body.get("result")

        if isinstance(result, list):

            return [
                cls.normalize_record(item)
                for item in result
                if isinstance(item, dict)
            ]

        if isinstance(result, dict):

            nested = cls.parse_dataset(result)

            if nested is not None:
                return nested

        # ----------------------------------------------
        # IMPORTANT:
        #
        # YOUR CURRENT ERROR COMES HERE.
        #
        # Bright Data returned ONE object:
        #
        # {
        #   "stock": "...",
        #   "url": "...",
        #   "input": {...}
        # }
        #
        # Accept that object as one record.
        # ----------------------------------------------

        if any(
            key in body
            for key in (
                "product_name",
                "Product Name",
                "product",
                "name",
                "title",
                "price",
                "Price",
                "stock",
                "Stock",
                "availability",
                "Availability",
                "url",
            )
        ):

            return [
                cls.normalize_record(body)
            ]

        return None

    # --------------------------------------------------
    # GET DATASET
    # --------------------------------------------------

    def dataset(
        self,
        snapshot_id: str,
    ) -> Optional[List[Dict[str, Any]]]:

        response = requests.get(
            f"{BASE_URL}/dca/dataset",
            params={
                "id": snapshot_id,
            },
            headers=self.headers,
            timeout=60,
        )

        try:
            body = response.json()
        except ValueError:
            body = response.text

        if response.status_code >= 400:

            raise RuntimeError(
                f"Bright Data dataset error "
                f"{response.status_code}: {body}"
            )

        return self.parse_dataset(body)

    # --------------------------------------------------
    # COLLECT
    # --------------------------------------------------

    def collect(
        self,
        inputs: List[Dict[str, Any]],
        timeout: int = 600,
        poll_interval: int = 5,
    ) -> Tuple[List[Dict[str, Any]], str]:

        snapshot_id = self.trigger(
            inputs
        )

        start_time = time.time()

        while (
            time.time() - start_time
            < timeout
        ):

            data = self.dataset(
                snapshot_id
            )

            if isinstance(data, list):

                return (
                    data,
                    snapshot_id,
                )

            time.sleep(
                poll_interval
            )

        raise RuntimeError(
            "Timed out waiting for Bright Data "
            "dataset. "
            f"Collection ID: {snapshot_id}"
        )

    # --------------------------------------------------
    # SELF HEAL
    # --------------------------------------------------

    def self_heal(
        self,
        prompt: str,
    ) -> Dict[str, Any]:

        response = requests.post(
            f"{BASE_URL}/dca/collectors/"
            f"{self.collector}/refactor_template",
            headers=self.headers,
            json={
                "prompt": prompt,
            },
            timeout=60,
        )

        try:
            result = response.json()
        except ValueError:
            result = {
                "raw_response": response.text
            }

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

    # --------------------------------------------------
    # SELF HEAL PROGRESS
    # --------------------------------------------------

    def self_heal_progress(
        self,
    ) -> Dict[str, Any]:

        response = requests.get(
            f"{BASE_URL}/dca/collectors/"
            f"{self.collector}/refactor_template/"
            "progress",
            headers=self.headers,
            timeout=60,
        )

        try:
            result = response.json()
        except ValueError:
            result = {
                "raw_response": response.text
            }

        if response.status_code >= 400:

            raise RuntimeError(
                "Bright Data Self-Healing progress "
                f"error {response.status_code}: {result}"
            )

        if isinstance(result, dict):
            return result

        return {
            "result": result
    }
