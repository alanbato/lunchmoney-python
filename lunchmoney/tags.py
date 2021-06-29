from typing import Optional

from pydantic import BaseModel


class Tag(BaseModel):
    id: int
    name: str
    description: Optional[str]
