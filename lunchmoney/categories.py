from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Category(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=40)
    description: Optional[str] = Field(..., max_length=140)
    is_income: bool
    exclude_from_budget: bool
    exclude_from_totals: bool
    updated_at: datetime
    created_at: datetime
    is_group: bool
    group_id: Optional[int]
