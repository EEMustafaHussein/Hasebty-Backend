"""Helpers so every endpoint returns the same response shape."""

from typing import Any

from fastapi import Query
from pydantic import BaseModel

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


class PageParams(BaseModel):
    page: int = 1
    limit: int = DEFAULT_LIMIT

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def page_params(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Items per page"),
) -> PageParams:
    return PageParams(page=page, limit=limit)


def success(data: Any, message: str = "Request completed successfully") -> dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def paginated(
    items: list[Any],
    total: int,
    params: PageParams,
    message: str = "Request completed successfully",
) -> dict[str, Any]:
    """Same shape as `success`, plus a `meta` block so the apps can load more pages."""
    response = success(items, message)
    response["meta"] = {"page": params.page, "limit": params.limit, "total": total}
    return response
