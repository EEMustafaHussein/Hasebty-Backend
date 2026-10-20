from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
