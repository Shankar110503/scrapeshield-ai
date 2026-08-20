    import os
import time
import requests


BASE = "https://api.brightdata.com"


class BrightDataClient:

    def __init__(self):
        self.token = os.getenv("BRIGHT_DATA_API_TOKEN")
        self.collector = os.getenv("BRIGHT_DATA_COLLECTOR_ID")

        if not self.token:
            raise RuntimeError(
                "BRIGHT_DATA_API_TOKEN is missing."
            )

        if not self.collector:
            raise RuntimeError(
                "BRIGHT_DATA_COLLECTOR_ID is missing."
            )

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
                "queue_next": "1",
            },
            headers=self.headers,
            json=inputs,
            timeout=60,
        )

        try:
            body = response.json()
        except Exception:
            body = response.text

        if response.status_code >= 400:
            raise RuntimeError(
                f"Bright Data trigger error "
                f"{response.status_code}: {body}"
            )

        collection_id = body.get("collection_id")

        if not collection_id:
            raise RuntimeError(
                f"Bright Data did not return collection_id: {body}"
            )

        return collection_id

    def dataset(self, snapshot_id):

        response = requests.get(
            f"{BASE}/dca/dataset",
            params={
                "id": snapshot_id
            },
            headers={
                "Authorization": f"Bearer {self.token}"
            },
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

        if isinstance(body, dict):

            if body.get("status") == "building":
                return None

            raise RuntimeError(
                f"Bright Data dataset status: {body}"
            )

        if isinstance(body, list):
            return body

        return None

    def collect(self, inputs, timeout=900):

        collection_id = self.trigger(inputs)

        start = time.time()

        while time.time() - start < timeout:

            data = self.dataset(collection_id)

            if data is not None:
                return data, collection_id

            time.sleep(5)

        raise RuntimeError(
            "Timed out waiting for Bright Data dataset. "
            f"Collection ID: {collection_id}"
        )
