"""Small data helpers used by the dashboard."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


DEFAULT_REQUIRED_FIELDS = ["product_name", "price", "stock"]


def normalize_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []

    for record in records:
        if not isinstance(record, dict):
            continue
        normalized.append(dict(record))

    return normalized


def missing_fields(
    records: List[Dict[str, Any]],
    required_fields: List[str] | None = None,
) -> List[str]:
    required = required_fields or DEFAULT_REQUIRED_FIELDS

    if not records:
        return list(required)

    missing: List[str] = []

    for field in required:
        found = False

        for row in records:
            value = row.get(field)
            if value is not None and str(value).strip() != "":
                found = True
                break

        if not found:
            missing.append(field)

    return missing


def add_demo_repair(
    records: List[Dict[str, Any]],
    missing: List[str],
) -> List[Dict[str, Any]]:
    """Repair demo data without changing existing values."""
    repaired = [dict(row) for row in records]

    for index, row in enumerate(repaired):
        if "price" in missing and not row.get("price"):
            demo_prices = ["₹59,999", "₹74,999", "₹89,999"]
            row["price"] = demo_prices[index % len(demo_prices)]

        if "product_name" in missing and not row.get("product_name"):
            row["product_name"] = f"Laptop {chr(65 + index)}"

        if "stock" in missing and not row.get("stock"):
            row["stock"] = "In stock" if index < 2 else "Out of stock"

    return repaired
