from pydantic import BaseModel, Field


class PartCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    socket: str | None = None
    ram_type: str | None = None
    form_factor: str | None = None
    wattage: int | None = Field(default=None, ge=0)
    specs: str | None = None
    image_url: str | None = Field(default=None, max_length=500, pattern=r"^(https?://|/static/)")


class PartPublic(PartCreate):
    id: int
