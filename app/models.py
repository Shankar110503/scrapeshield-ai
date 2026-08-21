from __future__ import annotations

from typing import Any, Dict, Iterable, List

DEFAULT_REQUIRED_FIELDS = ["product_name", "price", "stock"]


def normalize_records(
    records: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        dict(row)
        for row in records
        if isinstance(row, dict)
    ]


def missing_fields(
    records: List[Dict[str, Any]],
    required_fields: List[str] | None = None,
) -> List[str]:
    required = required_fields or DEFAULT_REQUIRED_FIELDS
    missing: List[str] = []

    for field in required:
        if not any(
            row.get(field) is not None
            and str(row.get(field)).strip() != ""
            for row in records
        ):
            missing.append(field)

    return missing


def add_demo_repair(
    records: List[Dict[str, Any]],
    missing: List[str],
) -> List[Dict[str, Any]]:
    repaired = [dict(row) for row in records]

    prices = ["₹59,999", "₹74,999", "₹89,999"]

    for i, row in enumerate(repaired):
        if "product_name" in missing and not row.get("product_name"):
            row["product_name"] = f"Laptop {chr(65 + i)}"

        if "price" in missing and not row.get("price"):
            row["price"] = prices[i % len(prices)]

        if "stock" in missing and not row.get("stock"):
            row["stock"] = "In stock" if i < 2 else "Out of stock"

    return repaired
