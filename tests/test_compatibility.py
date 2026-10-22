import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Category, Part
from app.services.compatibility_service import find_problems, required_watts


def part(name: str, **fields: object) -> Part:
    """A part that is never saved: the rules only read its fields."""
    return Part(category_id=1, name=name, price=100, stock=5, **fields)


# ---------- Rules 2-5 on their own (no database) ----------


def test_rule_2_cpu_must_fit_the_motherboard_socket() -> None:
    cpu = part("Ryzen 5 7600", socket="AM5")
    board = part("PRIME Z790-P", socket="LGA1700", ram_type="DDR5")

    warnings = find_problems({"CPU": cpu, "Motherboard": board})

    assert warnings == ["CPU Ryzen 5 7600 (AM5) does not fit motherboard PRIME Z790-P (LGA1700)"]


def test_rule_2_same_socket_is_fine_even_with_different_letter_case() -> None:
    cpu = part("Ryzen 5 7600", socket="am5")
    board = part("B650M-A", socket="AM5")

    assert find_problems({"CPU": cpu, "Motherboard": board}) == []


def test_rule_3_ddr4_ram_on_a_ddr5_motherboard_is_a_warning() -> None:
    ram = part("Kingston Fury 16GB DDR4", ram_type="DDR4")
    board = part("B650M-A", socket="AM5", ram_type="DDR5")

    warnings = find_problems({"RAM": ram, "Motherboard": board})

    assert len(warnings) == 1
    assert "RAM" in warnings[0]


def test_rule_4_atx_board_in_a_mini_itx_case_is_a_warning() -> None:
    board = part("TUF B650-PLUS", form_factor="ATX")
    case = part("Small Case", form_factor="Mini-ITX")

    warnings = find_problems({"Motherboard": board, "Case": case})

    assert len(warnings) == 1
    assert "does not fit case" in warnings[0]


def test_rule_4_smaller_board_fits_a_bigger_case() -> None:
    board = part("B650M-A", form_factor="mATX")
    case = part("Corsair 4000D", form_factor="ATX")

    assert find_problems({"Motherboard": board, "Case": case}) == []


def test_rule_5_300w_psu_is_too_weak_for_a_450w_build() -> None:
    cpu = part("i7-13700K", wattage=125)
    gpu = part("RTX 4080", wattage=325)
    psu = part("Small PSU", wattage=300)

    warnings = find_problems({"CPU": cpu, "GPU": gpu, "PSU": psu})

    assert len(warnings) == 1
    assert "Power supply" in warnings[0]


def test_rule_5_margin_is_20_percent() -> None:
    cpu = part("i7-13700K", wattage=125)
    gpu = part("RTX 4080", wattage=325)

    assert required_watts([cpu, gpu]) == 540  # 450 W + 20%
    assert find_problems({"CPU": cpu, "GPU": gpu, "PSU": part("PSU", wattage=540)}) == []
    assert len(find_problems({"CPU": cpu, "GPU": gpu, "PSU": part("PSU", wattage=539)})) == 1


def test_rules_need_both_parts_before_checking() -> None:
    cpu = part("Ryzen 5 7600", socket="AM5")

    assert find_problems({"CPU": cpu}) == []


def test_unknown_values_are_not_reported_as_problems() -> None:
    board = part("Board without size", socket="AM5")
    case = part("Corsair 4000D", form_factor="ATX")

    assert find_problems({"Motherboard": board, "Case": case}) == []


# ---------- Through the API: /builds/{id}/check and rule 6 ----------


@pytest.fixture
def pc_parts(session: Session) -> dict[str, int]:
    """Adds the categories and parts a full build needs and returns their ids."""
    cpu_category = session.exec(select(Category).where(Category.name == "CPU")).one()
    categories = {"CPU": cpu_category}
    for name in ["Motherboard", "RAM", "Case", "PSU"]:
        category = Category(name=name)
        session.add(category)
        session.commit()
        session.refresh(category)
        categories[name] = category

    def add(category: str, name: str, **fields: object) -> int:
        new_part = Part(
            category_id=categories[category].id or 0, name=name, price=100, stock=5, **fields
        )
        session.add(new_part)
        session.commit()
        session.refresh(new_part)
        return new_part.id or 0

    return {
        "cpu": add("CPU", "AMD Ryzen 5 7600", socket="AM5", wattage=65),
        "intel_board": add(
            "Motherboard", "ASUS PRIME Z790-P", socket="LGA1700", ram_type="DDR5", form_factor="ATX"
        ),
        "amd_board": add(
            "Motherboard",
            "ASUS TUF GAMING B650-PLUS",
            socket="AM5",
            ram_type="DDR5",
            form_factor="ATX",
        ),
        "ram": add("RAM", "Kingston Fury 32GB DDR5", ram_type="DDR5"),
        "case": add("Case", "Corsair 4000D Airflow", form_factor="ATX"),
        "psu": add("PSU", "Cooler Master MWE 650", wattage=650),
    }


def build_ids(parts: dict[str, int], board: str) -> list[int]:
    return [parts["cpu"], parts[board], parts["ram"], parts["case"], parts["psu"]]


def test_check_shows_a_warning_for_a_part_that_does_not_fit(
    client: TestClient, pc_parts: dict[str, int], customer: dict[str, str]
) -> None:
    body = {"name": "Demo PC", "part_ids": build_ids(pc_parts, "intel_board")}
    build = client.post("/builds", json=body, headers=customer).json()["data"]

    check = client.get(f"/builds/{build['id']}/check", headers=customer).json()["data"]

    assert check["warnings"] == [
        "CPU AMD Ryzen 5 7600 (AM5) does not fit motherboard ASUS PRIME Z790-P (LGA1700)"
    ]
    assert check["total"] == 500


def test_rule_6_build_with_a_problem_cannot_be_ordered(
    client: TestClient, pc_parts: dict[str, int], customer: dict[str, str]
) -> None:
    body = {"name": "Demo PC", "part_ids": build_ids(pc_parts, "intel_board")}
    build = client.post("/builds", json=body, headers=customer).json()["data"]

    response = client.post("/orders", json={"build_id": build["id"]}, headers=customer)

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert client.get("/me/orders", headers=customer).json()["data"] == []


def test_swapping_the_part_clears_the_warning_and_the_order_works(
    client: TestClient, pc_parts: dict[str, int], customer: dict[str, str]
) -> None:
    body = {"name": "Demo PC", "part_ids": build_ids(pc_parts, "intel_board")}
    build = client.post("/builds", json=body, headers=customer).json()["data"]

    fixed = {"name": "Demo PC", "part_ids": build_ids(pc_parts, "amd_board")}
    assert client.put(f"/builds/{build['id']}", json=fixed, headers=customer).status_code == 200
    check = client.get(f"/builds/{build['id']}/check", headers=customer).json()["data"]
    order = client.post("/orders", json={"build_id": build["id"]}, headers=customer)

    assert check["warnings"] == []
    assert order.status_code == 201
