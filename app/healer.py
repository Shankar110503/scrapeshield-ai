"""Self-healing helpers."""

from __future__ import annotations

from typing import Any, Dict, List

from .brightdata import BrightDataClient


def build_healing_prompt(missing: List[str]) -> str:
    fields = ", ".join(missing) if missing else "the required schema"

    return (
        "The latest collection is missing: "
        f"{fields}. "
        "Repair the extraction while preserving the existing output schema "
        "and returning all required fields."
    )


def run_self_heal(
    client: BrightDataClient,
    missing: List[str],
) -> Dict[str, Any]:
    return client.self_heal(build_healing_prompt(missing))
