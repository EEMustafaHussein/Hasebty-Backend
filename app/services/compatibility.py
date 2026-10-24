from app.models import Part

PSU_MARGIN = 1.2

FORM_FACTOR_SIZE = {"mini-itx": 1, "matx": 2, "atx": 3, "e-atx": 4}


def same(a: str, b: str) -> bool:
    return a.strip().lower() == b.strip().lower()


def check_compatibility(parts: dict[str, Part]) -> list[str]:

    warnings: list[str] = []
    cpu = parts.get("cpu")
    board = parts.get("motherboard")
    ram = parts.get("ram")
    case = parts.get("case")
    psu = parts.get("psu")

    if cpu and board and cpu.socket and board.socket and not same(cpu.socket, board.socket):
        warnings.append(
            f"The CPU socket ({cpu.socket}) does not match the motherboard socket ({board.socket})"
        )

    if ram and board and ram.ram_type and board.ram_type and not same(ram.ram_type, board.ram_type):
        warnings.append(
            f"The RAM type ({ram.ram_type}) does not match the motherboard ({board.ram_type})"
        )

    if board and case and board.form_factor and case.form_factor:
        board_size = FORM_FACTOR_SIZE.get(board.form_factor.strip().lower())
        case_size = FORM_FACTOR_SIZE.get(case.form_factor.strip().lower())
        if board_size and case_size and board_size > case_size:
            warnings.append(
                f"The motherboard ({board.form_factor}) is too big for the case "
                f"({case.form_factor})"
            )

    if psu and psu.wattage:
        needed = estimate_consumption(parts)
        if needed > 0 and psu.wattage < needed * PSU_MARGIN:
            warnings.append(
                f"The power supply ({psu.wattage} W) is too weak: the build needs about "
                f"{needed} W, and with the margin at least {needed * PSU_MARGIN:.0f} W"
            )

    return warnings


def estimate_consumption(parts: dict[str, Part]) -> int:
    """The wattage of every part except the power supply."""
    return sum(part.wattage or 0 for name, part in parts.items() if name != "psu")
