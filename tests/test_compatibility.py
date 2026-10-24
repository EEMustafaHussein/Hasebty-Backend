from app.models import Part
from app.services.compatibility import check_compatibility, estimate_consumption


def part(**fields: object) -> Part:
    values: dict[str, object] = {"category_id": 1, "name": "x", "price": 1, "stock": 1}
    values.update(fields)
    return Part(**values)  # type: ignore[arg-type]


def test_rule_2_am5_cpu_with_lga1700_board_gives_a_warning() -> None:
    parts = {"cpu": part(socket="AM5"), "motherboard": part(socket="LGA1700")}

    warnings = check_compatibility(parts)

    assert len(warnings) == 1
    assert "AM5" in warnings[0] and "LGA1700" in warnings[0]


def test_rule_2_same_socket_is_fine_even_with_different_capitals() -> None:
    parts = {"cpu": part(socket="am5"), "motherboard": part(socket="AM5 ")}

    assert check_compatibility(parts) == []


def test_rule_3_ddr4_ram_with_ddr5_board_gives_a_warning() -> None:
    parts = {"ram": part(ram_type="DDR4"), "motherboard": part(ram_type="DDR5")}

    warnings = check_compatibility(parts)

    assert len(warnings) == 1
    assert "DDR4" in warnings[0] and "DDR5" in warnings[0]


def test_rule_3_matching_ram_is_fine() -> None:
    parts = {"ram": part(ram_type="DDR5"), "motherboard": part(ram_type="DDR5")}

    assert check_compatibility(parts) == []


def test_rule_4_atx_board_in_a_mini_itx_case_gives_a_warning() -> None:
    parts = {"motherboard": part(form_factor="ATX"), "case": part(form_factor="Mini-ITX")}

    warnings = check_compatibility(parts)

    assert len(warnings) == 1
    assert "too big" in warnings[0]


def test_rule_4_smaller_or_equal_board_fits() -> None:
    assert (
        check_compatibility(
            {"motherboard": part(form_factor="mATX"), "case": part(form_factor="ATX")}
        )
        == []
    )
    assert (
        check_compatibility(
            {"motherboard": part(form_factor="ATX"), "case": part(form_factor="ATX")}
        )
        == []
    )
    assert (
        check_compatibility(
            {"motherboard": part(form_factor="Mini-ITX"), "case": part(form_factor="mATX")}
        )
        == []
    )


def test_rule_4_ematx_board_does_not_fit_an_atx_case() -> None:
    parts = {"motherboard": part(form_factor="E-ATX"), "case": part(form_factor="ATX")}

    assert len(check_compatibility(parts)) == 1


def test_rule_5_300w_psu_with_a_450w_build_gives_a_warning() -> None:
    parts = {
        "cpu": part(wattage=150),
        "gpu": part(wattage=300),
        "psu": part(wattage=300),
    }

    assert estimate_consumption(parts) == 450
    warnings = check_compatibility(parts)

    assert len(warnings) == 1
    assert "450" in warnings[0] and "540" in warnings[0]


def test_rule_5_the_margin_counts_psu_exactly_at_the_limit_is_fine() -> None:

    parts = {"cpu": part(wattage=200), "gpu": part(wattage=300), "psu": part(wattage=600)}

    assert check_compatibility(parts) == []


def test_rule_5_one_watt_under_the_limit_is_a_warning() -> None:
    parts = {"cpu": part(wattage=200), "gpu": part(wattage=300), "psu": part(wattage=599)}

    assert len(check_compatibility(parts)) == 1


def test_rule_5_the_psu_does_not_count_as_consumption() -> None:
    parts = {"cpu": part(wattage=100), "psu": part(wattage=650)}

    assert estimate_consumption(parts) == 100


def test_unfinished_build_has_no_warnings() -> None:
    assert check_compatibility({}) == []
    assert check_compatibility({"cpu": part(socket="AM5")}) == []
    assert check_compatibility({"psu": part(wattage=300)}) == []


def test_part_with_missing_data_is_skipped() -> None:
    parts = {"cpu": part(socket=None), "motherboard": part(socket="AM5")}

    assert check_compatibility(parts) == []


def test_several_problems_give_several_warnings() -> None:
    parts = {
        "cpu": part(socket="AM5", wattage=100),
        "motherboard": part(socket="AM4", ram_type="DDR4", form_factor="ATX"),
        "ram": part(ram_type="DDR5"),
        "case": part(form_factor="Mini-ITX"),
        "psu": part(wattage=100),
    }

    assert len(check_compatibility(parts)) == 4
