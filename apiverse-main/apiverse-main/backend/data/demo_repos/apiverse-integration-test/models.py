from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Order:
    order_id: int
    status: str
    amount: int
    tracking_number: Optional[str] = None
