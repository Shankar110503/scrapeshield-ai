from dataclasses import dataclass
from typing import List


@dataclass
class FieldSpec:
    name: str
    description: str


@dataclass
class HealthReport:
    healthy: bool
    missing_fields: List[str]
    row_count: int
    message: str
