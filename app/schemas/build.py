from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.part import PartPublic


class BuildCreate(BaseModel):
    name: str = Field(min_length=1)
    part_ids: list[int] = []


class BuildPublic(BaseModel):
    id: int
    name: str
    customer_id: int
    created_at: datetime
    part_ids: list[int] = []
    parts: list[PartPublic] = []
    total: float = 0
    warnings: list[str] = []


class BuildCheckPublic(BaseModel):
    build_id: int
    warnings: list[str]
    total: float
