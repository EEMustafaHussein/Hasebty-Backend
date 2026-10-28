import os

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.models import Category, Part
from app.responses import PageParams
from app.schemas.part import PartPublic
from app.utils import require_id


def image_link(image_url: str | None) -> str | None:
    """A picture on our own server (/static/...) becomes a full link the apps can open."""
    if image_url and image_url.startswith("/"):
        return os.getenv("PUBLIC_BASE_URL", "").rstrip("/") + image_url
    return image_url


def part_to_public(part: Part) -> PartPublic:
    return PartPublic(
        id=require_id(part.id),
        category_id=part.category_id,
        name=part.name,
        price=part.price,
        stock=part.stock,
        socket=part.socket,
        ram_type=part.ram_type,
        form_factor=part.form_factor,
        wattage=part.wattage,
        specs=part.specs,
        image_url=image_link(part.image_url),
    )


def list_parts(
    session: Session,
    params: PageParams,
    category: str | None = None,
    search: str | None = None,
    in_stock: bool | None = None,
) -> tuple[list[Part], int]:
    """Return one page of parts and the total number of matching parts."""
    statement = select(Part)

    if category:
        if category.isdigit():
            statement = statement.where(Part.category_id == int(category))
        else:
            statement = statement.join(Category, col(Part.category_id) == col(Category.id)).where(
                func.lower(Category.name) == category.strip().lower()
            )

    if search:
        statement = statement.where(col(Part.name).icontains(search.strip(), autoescape=True))

    if in_stock is True:
        statement = statement.where(col(Part.stock) > 0)
    elif in_stock is False:
        statement = statement.where(col(Part.stock) <= 0)

    total = session.exec(select(func.count()).select_from(statement.subquery())).one()

    page = session.exec(
        statement.order_by(col(Part.id)).offset(params.offset).limit(params.limit)
    ).all()

    return list(page), total
