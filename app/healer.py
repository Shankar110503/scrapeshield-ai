from __future__ import annotations

from typing import List

from app.brightdata import BrightDataClient


def build_healing_prompt(missing: List[str]) -> str:
    fields = ", ".join(missing) if missing else "the required schema"
    return (
        f"The latest collection is missing: {fields}. "
        "Repair the extraction while preserving the existing output schema "
        "and returning all required fields."
    )


def run_self_heal(
    client: BrightDataClient,
    missing: List[str],
):
    return client.self_heal(build_healing_prompt(missing))
