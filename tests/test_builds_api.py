from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Category, Part


def part_id(session: Session, name: str) -> int:
    return session.exec(select(Part).where(Part.name == name)).one().id or 0


def add_second_cpu(session: Session) -> int:
    cpu_category = session.exec(select(Category).where(Category.name == "CPU")).one()
    cpu = Part(category_id=cpu_category.id or 0, name="Ryzen 7 5700X", price=200, stock=5)
    session.add(cpu)
    session.commit()
    session.refresh(cpu)
    return cpu.id or 0


def create_build(client: TestClient, headers: dict[str, str], ids: list[int]) -> dict:
    response = client.post("/builds", json={"name": "My PC", "part_ids": ids}, headers=headers)
    assert response.status_code == 201
    return response.json()["data"]


def test_create_build_returns_parts_and_total(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    ids = [part_id(session, "Ryzen 5 5600"), part_id(session, "RTX 4060")]

    build = create_build(client, customer, ids)

    assert sorted(build["part_ids"]) == sorted(ids)
    assert len(build["parts"]) == 2
    assert build["total"] == 420


def test_rule_1_second_part_of_a_category_replaces_the_first(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    first_cpu = part_id(session, "Ryzen 5 5600")
    second_cpu = add_second_cpu(session)

    build = create_build(client, customer, [first_cpu, second_cpu])

    assert build["part_ids"] == [second_cpu]
    assert build["total"] == 200


def test_update_build_changes_parts_and_total(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    first_cpu = part_id(session, "Ryzen 5 5600")
    gpu = part_id(session, "RTX 4060")
    second_cpu = add_second_cpu(session)
    build = create_build(client, customer, [first_cpu, gpu])

    response = client.put(
        f"/builds/{build['id']}",
        json={"name": "Better PC", "part_ids": [second_cpu, gpu]},
        headers=customer,
    )

    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["name"] == "Better PC"
    assert sorted(updated["part_ids"]) == sorted([second_cpu, gpu])
    assert updated["total"] == 500


def test_update_build_with_the_same_parts_works(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    ids = [part_id(session, "Ryzen 5 5600")]
    build = create_build(client, customer, ids)

    response = client.put(
        f"/builds/{build['id']}", json={"name": "Same", "part_ids": ids}, headers=customer
    )

    assert response.status_code == 200
    assert response.json()["data"]["part_ids"] == ids


def test_unknown_part_is_404_and_nothing_is_saved(
    client: TestClient, customer: dict[str, str]
) -> None:
    response = client.post("/builds", json={"name": "Bad", "part_ids": [9999]}, headers=customer)

    assert response.status_code == 404
    assert client.get("/me/builds", headers=customer).json()["data"] == []


def test_build_needs_a_name(client: TestClient, customer: dict[str, str]) -> None:
    response = client.post("/builds", json={"name": "", "part_ids": []}, headers=customer)

    assert response.status_code == 422
    assert "name" in response.json()["errors"]


def test_saved_builds_are_listed_with_totals(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    create_build(client, customer, [part_id(session, "Ryzen 5 5600")])
    create_build(client, customer, [part_id(session, "RTX 4060")])

    response = client.get("/me/builds", headers=customer)

    body = response.json()
    assert response.status_code == 200
    assert body["meta"]["total"] == 2
    assert [b["total"] for b in body["data"]] == [300, 120]  # newest first


def test_customers_only_see_their_own_builds(
    client: TestClient,
    session: Session,
    customer: dict[str, str],
    other_customer: dict[str, str],
) -> None:
    build = create_build(client, customer, [part_id(session, "Ryzen 5 5600")])

    assert client.get("/me/builds", headers=other_customer).json()["data"] == []
    assert client.get(f"/builds/{build['id']}", headers=other_customer).status_code == 404
    assert client.get(f"/builds/{build['id']}/check", headers=other_customer).status_code == 404
    put = client.put(
        f"/builds/{build['id']}", json={"name": "Hack", "part_ids": []}, headers=other_customer
    )
    assert put.status_code == 404


def test_rule_7_check_total_equals_the_build_total(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    build = create_build(
        client, customer, [part_id(session, "Ryzen 5 5600"), part_id(session, "RTX 4060")]
    )

    check = client.get(f"/builds/{build['id']}/check", headers=customer).json()["data"]

    assert check["total"] == build["total"] == 420
    assert check["warnings"] == []


def test_total_follows_a_price_change_made_by_staff(
    client: TestClient, session: Session, customer: dict[str, str], staff: dict[str, str]
) -> None:
    cpu = session.exec(select(Part).where(Part.name == "Ryzen 5 5600")).one()
    build = create_build(client, customer, [cpu.id or 0])

    body = {"category_id": cpu.category_id, "name": cpu.name, "price": 100, "stock": cpu.stock}
    assert client.put(f"/parts/{cpu.id}", json=body, headers=staff).status_code == 200

    saved = client.get(f"/builds/{build['id']}", headers=customer).json()["data"]
    assert saved["total"] == 100


def test_builds_survive_a_new_login(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    from tests.conftest import CUSTOMER_PHONE, login

    create_build(client, customer, [part_id(session, "Ryzen 5 5600")])

    new_session_headers = login(client, CUSTOMER_PHONE)

    builds = client.get("/me/builds", headers=new_session_headers).json()["data"]
    assert len(builds) == 1


def test_staff_cannot_create_builds(client: TestClient, staff: dict[str, str]) -> None:
    response = client.post("/builds", json={"name": "X", "part_ids": []}, headers=staff)

    assert response.status_code == 403


def test_builds_need_a_login(client: TestClient) -> None:
    assert client.post("/builds", json={"name": "X", "part_ids": []}).status_code == 401
    assert client.get("/me/builds").status_code == 401
