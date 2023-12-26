from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Component:
    name: str
    version: str
    registry_url: str
    homepage_url: Optional[str]
    description: Optional[str]
    declared_licenses: List[str]
    raw: Dict[str, Any]
