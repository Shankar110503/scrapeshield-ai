from typing import Any, Dict, List

from models import FieldSpec, HealthReport


def check_health(
    rows: List[Dict[str, Any]],
    schema: List[FieldSpec],
) -> HealthReport:
    """Check whether required fields are present in collected data."""

    if not rows:
        return HealthReport(
            healthy=False,
            missing_fields=[field.name for field in schema],
            row_count=0,
            message="No rows returned by the scraper.",
        )

    missing_fields = []

    for field in schema:
        has_value = any(
            str(row.get(field.name, "")).strip()
            for row in rows
        )

        if not has_value:
            missing_fields.append(field.name)

    if not missing_fields:
        return HealthReport(
            healthy=True,
            missing_fields=[],
            row_count=len(rows),
            message="Extraction healthy. All required fields are present.",
        )

    return HealthReport(
        healthy=False,
        missing_fields=missing_fields,
        row_count=len(rows),
        message=(
            "Extraction failure detected. Missing fields: "
            + ", ".join(missing_fields)
        ),
    )
