from dataclasses import dataclass
from typing import Optional

@dataclass
class StoreItem:
    id: int
    name: str
    status: str
