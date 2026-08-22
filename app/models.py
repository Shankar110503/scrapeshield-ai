from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ScraperJob:
    collector_id: str
    target_url: str
    required_fields: List[str]
    status: str = "PENDING"
    last_run_data: Optional[Dict] = None

@dataclass
class HealingReport:
    collector_id: str
    healed_fields: List[str]
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    
