from pydantic import BaseModel, Field
class BuildCreate(BaseModel):
    name: str = Field(min_length=1)
    part_ids: list[int] = []
class BuildPublic(BaseModel):
    id: int
    name: str
    customer_id: int
    part_ids: list[int] = []
class BuildCheckPublic(BaseModel):
    build_id: int
    warnings: list[str]
    total: float
