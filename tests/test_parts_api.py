from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Category, Part


def category_id(session: Session, name: str) -> int:
    category = session.exec(select(Category).where(Category.name == name)).one()
    return category.id or 0


def new_part_body(session: Session, **changes: object) -> dict[str, object]:
    body: dict[str, object] = {
        "category_id": category_id(session, "CPU"),
        "name": "Ryzen 7 5700X",
        "price": 200,
        "stock": 5,
        "socket": "AM4",
    }
    body.update(changes)
    return body


def test_list_parts_is_public_and_uses_the_response_shape(client: TestClient) -> None:
    response = client.get("/parts")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"]
    assert len(body["data"]) == 2
    assert body["meta"] == {"page": 1, "limit": 50, "total": 2}


def test_filter_parts_by_category_name_and_id(client: TestClient, session: Session) -> None:
    by_name = client.get("/parts", params={"category": "cpu"}).json()["data"]
    by_id = client.get("/parts", params={"category": category_id(session, "CPU")}).json()["data"]

    assert [p["name"] for p in by_name] == ["Ryzen 5 5600"]
    assert by_id == by_name


def test_unknown_category_returns_an_empty_list(client: TestClient) -> None:
    response = client.get("/parts", params={"category": "Toaster"})

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_search_parts_by_name(client: TestClient) -> None:
    data = client.get("/parts", params={"search": "rtx"}).json()["data"]

    assert [p["name"] for p in data] == ["RTX 4060"]


def test_parts_are_paginated(client: TestClient) -> None:
    first = client.get("/parts", params={"limit": 1, "page": 1}).json()
    second = client.get("/parts", params={"limit": 1, "page": 2}).json()

    assert len(first["data"]) == 1 and len(second["data"]) == 1
    assert first["data"][0]["id"] != second["data"][0]["id"]
    assert first["meta"]["total"] == 2


def test_bad_pagination_is_a_422_not_a_500(client: TestClient) -> None:
    response = client.get("/parts", params={"limit": 1000})

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Validation failed"
    assert "limit" in body["errors"]


def test_get_part_details_and_404(client: TestClient) -> None:
    part_id = client.get("/parts").json()["data"][0]["id"]

    assert client.get(f"/parts/{part_id}").json()["data"]["id"] == part_id

    missing = client.get("/parts/9999")
    assert missing.status_code == 404
    assert missing.json() == {"success": False, "message": "Part not found", "errors": {}}


def test_unknown_url_uses_the_error_shape(client: TestClient) -> None:
    response = client.get("/nothing-here")

    assert response.status_code == 404
    assert response.json()["success"] is False


def test_staff_can_add_a_part(client: TestClient, session: Session, staff: dict[str, str]) -> None:
    response = client.post("/parts", json=new_part_body(session), headers=staff)

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Ryzen 7 5700X"
    assert len(client.get("/parts").json()["data"]) == 3


def test_staff_can_edit_price_and_stock(
    client: TestClient, session: Session, staff: dict[str, str]
) -> None:
    part = session.exec(select(Part).where(Part.name == "Ryzen 5 5600")).one()
    body = new_part_body(session, name=part.name, price=99.5, stock=3)

    response = client.put(f"/parts/{part.id}", json=body, headers=staff)

    assert response.status_code == 200
    shown = client.get(f"/parts/{part.id}").json()["data"]
    assert shown["price"] == 99.5
    assert shown["stock"] == 3


def test_customer_cannot_manage_parts(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    response = client.post("/parts", json=new_part_body(session), headers=customer)

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_managing_parts_needs_a_login(client: TestClient, session: Session) -> None:
    assert client.post("/parts", json=new_part_body(session)).status_code == 401


def test_part_with_negative_price_is_refused(
    client: TestClient, session: Session, staff: dict[str, str]
) -> None:
    response = client.post("/parts", json=new_part_body(session, price=-5), headers=staff)

    assert response.status_code == 422
    assert "price" in response.json()["errors"]


def test_part_with_unknown_category_is_404(
    client: TestClient, session: Session, staff: dict[str, str]
) -> None:
    response = client.post("/parts", json=new_part_body(session, category_id=999), headers=staff)

    assert response.status_code == 404
