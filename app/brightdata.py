import os
import time
import requests

BASE = "https://api.brightdata.com"


class BrightDataClient:
    def __init__(self):
        self.token = os.getenv("BRIGHT_DATA_API_TOKEN")
        self.collector = os.getenv("BRIGHT_DATA_COLLECTOR_ID")

        if not self.token or not self.collector:
            raise RuntimeError(
                "Set BRIGHT_DATA_API_TOKEN and BRIGHT_DATA_COLLECTOR_ID."
            )

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def dataset(self, snapshot_id):
    r = requests.get(
        f"{BASE}/dca/dataset",
        params={"id": snapshot_id},
        headers=self.headers,
        timeout=60,
    )

    try:
        body = r.json()
    except Exception:
        body = r.text

    if r.status_code >= 400:
        raise RuntimeError(
            f"Bright Data dataset error {r.status_code}: {body}"
        )

    if isinstance(body, list):
        return body

    if isinstance(body, dict):
        if body.get("status") == "building":
            return None

        raise RuntimeError(
            f"Bright Data dataset status: {body}"
        )

    return None

        if "collection_id" not in result:
            raise RuntimeError(
                f"Bright Data did not return collection_id: {result}"
            )

        return result["collection_id"]

    def dataset(self, snapshot_id):
    r = requests.get(
        f"{BASE}/dca/dataset",
        params={"id": snapshot_id},
        headers=self.headers,
        timeout=60,
    )

    try:
        body = r.json()
    except Exception:
        body = r.text

    if r.status_code >= 400:
        raise RuntimeError(
            f"Bright Data dataset error {r.status_code}: {body}"
        )

    if isinstance(body, list):
        return body

    if isinstance(body, dict):
        if body.get("status") == "building":
            return None

        raise RuntimeError(
            f"Bright Data dataset status: {body}"
        )

    return None

    def collect(self, inputs, timeout=600):
        sid = self.trigger(inputs)

        start = time.time()

        while time.time() - start < timeout:
            data = self.dataset(sid)

            if isinstance(data, list):
                return data, sid

            time.sleep(10)

        raise RuntimeError(
            f"Timed out waiting for Bright Data dataset. "
            f"Collection ID: {sid}"
        )

    def self_heal(self, prompt):
        r = requests.post(
            f"{BASE}/dca/collectors/{self.collector}/refactor_template",
            headers=self.headers,
            json={"prompt": prompt},
            timeout=60,
        )

        r.raise_for_status()

        return r.json() if r.content else {"status": "started"}

    def self_heal_progress(self):
        r = requests.get(
            f"{BASE}/dca/collectors/{self.collector}/refactor_template/progress",
            headers=self.headers,
            timeout=60,
        )

        r.raise_for_status()

        return r.json()
