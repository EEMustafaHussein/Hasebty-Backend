from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
class Build(SQLModel, table=True):
    __tablename__ = "builds"
    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="users.id", index=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
class BuildPart(SQLModel, table=True):
    __tablename__ = "build_parts"
    build_id: int = Field(primary_key=True, foreign_key="builds.id")
    category_id: int = Field(primary_key=True, foreign_key="categories.id")
    part_id: int = Field(foreign_key="parts.id")
