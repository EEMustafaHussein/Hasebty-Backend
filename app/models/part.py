from sqlmodel import Field, SQLModel


class Part(SQLModel, table=True):
    __tablename__ = "parts"
    id: int | None = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="categories.id", index=True)
    name: str
    price: float
    stock: int = 0
    socket: str | None = None
    ram_type: str | None = None
    form_factor: str | None = None
    wattage: int | None = None
    specs: str | None = None
    image_url: str | None = None
