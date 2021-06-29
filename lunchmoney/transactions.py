from enum import Enum
from typing import List, Optional, TypedDict, Union

from pydantic import BaseModel, Field

from .tags import Tag


class TransactionStatus(str, Enum):
    cleared = "cleared"
    uncleared = "uncleared"
    recurring = "recurring"
    recurring_suggested = "recurring_suggested"


class Transaction(BaseModel):
    id: Optional[int]
    date: str
    amount: float
    payee: Optional[str] = Field(..., max_length=140)
    currency: Optional[str]
    status: Optional[TransactionStatus] = TransactionStatus.uncleared
    category_id: Optional[int]
    asset_id: Optional[int]
    parent_id: Optional[int]
    plaid_account_id: Optional[int]
    is_group: Optional[bool]
    group_id: Optional[int]
    external_id: Optional[str] = Field(None, max_length=75)
    tags: Optional[List[Tag]]
    notes: Optional[str] = Field(None, max_length=350)


class TransactionDataRequired(TypedDict):
    date: str
    amount: Union[float, str]


class TransactionData(TransactionDataRequired, total=False):
    payee: str
    currency: str
    status: str
    category_id: int
    asset_id: int
    recurring_id: int
    external_id: str
    tags: str
    notes: str


class SplitDataRequied(TypedDict):
    date: str
    category_id: int
    amount: int


class SplitData(SplitDataRequied):
    notes: str
