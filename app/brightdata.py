import os
import time
import requests

BASE = "https://api.brightdata.com"


class BrightDataClient:
    def __init__(self):
        self.token = os.getenv("BRIGHT_DATA_API_TOKEN")
        self.collector = os.getenv("BRIGHT_DATA_COLLECTOR_ID")

        if not self.token:
            raise RuntimeError("BRIGHT_DATA_API_TOKEN is not set.")

        if not self.collector:
            raise RuntimeError("BRIGHT_DATA_COLLECTOR_ID is not set.")

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def trigger(self, inputs):
        response = requests.post(
            f"{BASE}/dca/trigger",
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
        except Exception:
            result = response.text

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data trigger error "
                f"{response.status_code}: {result}"
            )

        if not isinstance(result, dict):
            raise RuntimeError(
                f"Unexpected Bright Data response: {result}"
            )

        collection_id = result.get("collection_id")

        if not collection_id:
            raise RuntimeError(
                f"Bright Data did not return collection_id: {result}"
            )

        return collection_id

    def dataset(self, snapshot_id):
        response = requests.get(
            f"{BASE}/dca/dataset",
            params={"id": snapshot_id},
            headers=self.headers,
            timeout=60,
        )

        try:
            body = response.json()
        except Exception:
            body = response.text

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data dataset error "
                f"{response.status_code}: {body}"
            )

        if isinstance(body, list):
            return body

        if isinstance(body, dict):
            status = body.get("status")

            if status in {
                "building",
                "running",
                "pending",
                "starting",
            }:
                return None

            # Some Bright Data responses may contain the data
            # inside a result/data field.
            if isinstance(body.get("data"), list):
                return body["data"]

            if isinstance(body.get("results"), list):
                return body["results"]

            return None

        return None

    def collect(self, inputs, timeout=600):
        collection_id = self.trigger(inputs)

        start = time.time()

        while time.time() - start < timeout:
            data = self.dataset(collection_id)

            if isinstance(data, list):
                return data, collection_id

            time.sleep(10)

        raise RuntimeError(
            "Timed out waiting for Bright Data dataset. "
            f"Collection ID: {collection_id}"
        )

    def self_heal(self, prompt):
        response = requests.post(
            f"{BASE}/dca/collectors/"
            f"{self.collector}/refactor_template",
            headers=self.headers,
            json={"prompt": prompt},
            timeout=60,
        )

        response.raise_for_status()

        return (
            response.json()
            if response.content
            else {"status": "started"}
        )

    def self_heal_progress(self):
        response = requests.get(
            f"{BASE}/dca/collectors/"
            f"{self.collector}/refactor_template/progress",
            headers=self.headers,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()
