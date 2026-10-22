from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Category, Part


def add_part(session: Session, category: str, name: str, **fields: object) -> int:
    row = session.exec(select(Category).where(Category.name == category)).first()
    if row is None:
        row = Category(name=category)
        session.add(row)
        session.commit()
        session.refresh(row)

    values: dict[str, object] = {"price": 100, "stock": 5}
    values.update(fields)
    part = Part(category_id=row.id or 0, name=name, **values)  # type: ignore[arg-type]
    session.add(part)
    session.commit()
    session.refresh(part)
    return part.id or 0


def make_build(client: TestClient, headers: dict[str, str], ids: list[int]) -> int:
    response = client.post("/builds", json={"name": "PC", "part_ids": ids}, headers=headers)
    assert response.status_code == 201
    return int(response.json()["data"]["id"])


def check(client: TestClient, headers: dict[str, str], build_id: int) -> dict:
    response = client.get(f"/builds/{build_id}/check", headers=headers)
    assert response.status_code == 200
    return response.json()["data"]


def test_rule_2_check_warns_about_the_socket(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    cpu = add_part(session, "CPU", "Ryzen 7600", socket="AM5")
    board = add_part(session, "Motherboard", "Intel board", socket="LGA1700")

    result = check(client, customer, make_build(client, customer, [cpu, board]))

    assert len(result["warnings"]) == 1
    assert "socket" in result["warnings"][0]


def test_rule_3_check_warns_about_the_ram_type(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    board = add_part(session, "Motherboard", "DDR5 board", ram_type="DDR5")
    ram = add_part(session, "RAM", "DDR4 kit", ram_type="DDR4")

    result = check(client, customer, make_build(client, customer, [board, ram]))

    assert len(result["warnings"]) == 1
    assert "RAM" in result["warnings"][0]


def test_rule_4_check_warns_when_the_board_does_not_fit_the_case(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    board = add_part(session, "Motherboard", "ATX board", form_factor="ATX")
    case = add_part(session, "Case", "Tiny case", form_factor="Mini-ITX")
    result = check(client, customer, make_build(client, customer, [board, case]))
    assert len(result["warnings"]) == 1
    assert "too big" in result["warnings"][0]


def test_rule_5_check_warns_about_a_weak_power_supply(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    cpu = add_part(session, "CPU", "Hungry CPU", wattage=150)
    gpu = add_part(session, "GPU", "Hungry GPU", wattage=300)
    psu = add_part(session, "PSU", "Weak PSU", wattage=300)

    result = check(client, customer, make_build(client, customer, [cpu, gpu, psu]))

    assert len(result["warnings"]) == 1
    assert "power supply" in result["warnings"][0]


def test_a_good_build_has_no_warnings(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    cpu = add_part(session, "CPU", "Ryzen 7600", socket="AM5", wattage=65)
    board = add_part(
        session, "Motherboard", "B650", socket="AM5", ram_type="DDR5", form_factor="mATX"
    )
    ram = add_part(session, "RAM", "DDR5 kit", ram_type="DDR5")
    case = add_part(session, "Case", "Mid tower", form_factor="ATX")
    psu = add_part(session, "PSU", "650W", wattage=650)
    build_id = make_build(client, customer, [cpu, board, ram, case, psu])
    assert check(client, customer, build_id)["warnings"] == []


def test_the_build_response_also_shows_the_warnings(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    cpu = add_part(session, "CPU", "Ryzen 7600", socket="AM5")
    board = add_part(session, "Motherboard", "Intel board", socket="LGA1700")
    response = client.post(
        "/builds", json={"name": "PC", "part_ids": [cpu, board]}, headers=customer
    )

    assert len(response.json()["data"]["warnings"]) == 1


def test_rule_6_a_build_with_a_warning_cannot_be_ordered(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    cpu = add_part(session, "CPU", "Ryzen 7600", socket="AM5")
    board = add_part(session, "Motherboard", "Intel board", socket="LGA1700")
    build_id = make_build(client, customer, [cpu, board])
    response = client.post("/orders", json={"build_id": build_id}, headers=customer)

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert "compatibility" in response.json()["message"]
    assert client.get("/me/orders", headers=customer).json()["data"] == []


def test_swapping_the_wrong_part_clears_the_warning_and_the_order_works(
    client: TestClient, session: Session, customer: dict[str, str]
) -> None:
    cpu = add_part(session, "CPU", "Ryzen 7600", socket="AM5")
    wrong_board = add_part(session, "Motherboard", "Intel board", socket="LGA1700")
    right_board = add_part(session, "Motherboard", "AM5 board", socket="AM5")
    build_id = make_build(client, customer, [cpu, wrong_board])
    assert check(client, customer, build_id)["warnings"] != []
    swap = client.put(
        f"/builds/{build_id}", json={"name": "PC", "part_ids": [cpu, right_board]}, headers=customer
    )
    order = client.post("/orders", json={"build_id": build_id}, headers=customer)
    assert swap.status_code == 200
    assert check(client, customer, build_id)["warnings"] == []
    assert order.status_code == 201
