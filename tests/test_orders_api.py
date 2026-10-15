from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Part


def build_with_everything(client: TestClient, session: Session, headers: dict[str, str]) -> int:
    ids = [p.id for p in session.exec(select(Part)).all()]
    response = client.post("/builds", json={"name": "PC", "part_ids": ids}, headers=headers)
    return int(response.json()["data"]["id"])


def test_order_total_comes_from_the_api(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    build_id = build_with_everything(client, session, customer)

    response = client.post("/orders", json={"build_id": build_id}, headers=customer)

    assert response.status_code == 201
    assert response.json()["data"]["total_price"] == 420
    assert response.json()["data"]["status"] == "received"


def test_rule_8_part_without_stock_cannot_be_ordered(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    build_id = build_with_everything(client, session, customer)
    gpu = session.exec(select(Part).where(Part.name == "RTX 4060")).one()
    gpu.stock = 0
    session.add(gpu)
    session.commit()

    response = client.post("/orders", json={"build_id": build_id}, headers=customer)

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_empty_build_cannot_be_ordered(client: TestClient, customer: dict[str, str]) -> None:
    build = client.post("/builds", json={"name": "Empty", "part_ids": []}, headers=customer)

    response = client.post(
        "/orders", json={"build_id": build.json()["data"]["id"]}, headers=customer
    )

    assert response.status_code == 400


def test_rule_9_status_only_moves_forward(
    client: TestClient, session: Session, customer: dict[str, str], staff: dict[str, str]
) -> None:
    build_id = build_with_everything(client, session, customer)
    order_id = client.post("/orders", json={"build_id": build_id}, headers=customer).json()["data"][
        "id"
    ]

    ready = client.patch(f"/orders/{order_id}/status", json={"status": "ready"}, headers=staff)
    back = client.patch(f"/orders/{order_id}/status", json={"status": "assembling"}, headers=staff)

    assert ready.status_code == 200
    assert back.status_code == 400
    mine = client.get("/me/orders", headers=customer).json()["data"]
    assert mine[0]["status"] == "ready"


def test_customer_cannot_change_status_or_see_all_orders(
    client: TestClient, customer: dict[str, str]
) -> None:
    assert client.get("/orders", headers=customer).status_code == 403
    patch = client.patch("/orders/1/status", json={"status": "ready"}, headers=customer)
    assert patch.status_code == 403


def test_staff_can_filter_orders_by_status(
    client: TestClient, session: Session, customer: dict[str, str], staff: dict[str, str]
) -> None:
    build_id = build_with_everything(client, session, customer)
    client.post("/orders", json={"build_id": build_id}, headers=customer)

    received = client.get("/orders", params={"status": "received"}, headers=staff).json()
    ready = client.get("/orders", params={"status": "ready"}, headers=staff).json()

    assert received["meta"]["total"] == 1
    assert ready["data"] == []
