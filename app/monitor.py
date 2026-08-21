from __future__ import annotations

from typing import Any, Dict, List

from app.models import DEFAULT_REQUIRED_FIELDS, missing_fields


def inspect(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    missing = missing_fields(records, DEFAULT_REQUIRED_FIELDS)

    return {
        "healthy": not missing,
        "rows": len(records),
        "missing_fields": missing,
        "required_fields": DEFAULT_REQUIRED_FIELDS,
    }
