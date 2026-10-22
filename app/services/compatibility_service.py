import math

from app.models import Part

# Agreed in Week 1: the PSU must give at least 20% more power than the build uses.
PSU_MARGIN_PERCENT = 20

# Motherboard sizes from smallest to largest. A case fits boards up to its own size.
FORM_FACTOR_SIZE = {"MINI-ITX": 1, "ITX": 1, "MATX": 2, "MICRO-ATX": 2, "ATX": 3}


def different(first: str | None, second: str | None) -> bool:
    """True only when both values are known and they don't match (case and spaces ignored)."""
    if not first or not second:
        return False
    return first.strip().upper() != second.strip().upper()


def board_size(form_factor: str | None) -> int | None:
    return FORM_FACTOR_SIZE.get((form_factor or "").strip().upper())


def required_watts(parts: list[Part]) -> int:

    used = sum(part.wattage or 0 for part in parts)
    return math.ceil(used * (100 + PSU_MARGIN_PERCENT) / 100)


def check_cpu_socket(cpu: Part, board: Part) -> str | None:

    if different(cpu.socket, board.socket):
        return (
            f"CPU {cpu.name} ({cpu.socket}) does not fit motherboard {board.name} ({board.socket})"
        )
    return None


def check_ram_type(ram: Part, board: Part) -> str | None:

    if different(ram.ram_type, board.ram_type):
        return (
            f"RAM {ram.name} ({ram.ram_type}) does not fit "
            f"motherboard {board.name} ({board.ram_type})"
        )
    return None


def check_board_fits_case(board: Part, case: Part) -> str | None:

    board_value = board_size(board.form_factor)
    case_value = board_size(case.form_factor)
    if board_value and case_value and board_value > case_value:
        return (
            f"Motherboard {board.name} ({board.form_factor}) does not fit "
            f"case {case.name} ({case.form_factor})"
        )
    return None


def check_power_supply(psu: Part, other_parts: list[Part]) -> str | None:

    needed = required_watts(other_parts)
    psu_watts = psu.wattage or 0
    if psu_watts < needed:
        return (
            f"Power supply {psu.name} ({psu_watts} W) is too weak: this build needs "
            f"at least {needed} W (with a {PSU_MARGIN_PERCENT}% margin)"
        )
    return None


def find_problems(parts: dict[str, Part]) -> list[str]:

    cpu = parts.get("CPU")
    board = parts.get("Motherboard")
    ram = parts.get("RAM")
    case = parts.get("Case")
    psu = parts.get("PSU")

    results: list[str | None] = []
    if cpu and board:
        results.append(check_cpu_socket(cpu, board))
    if ram and board:
        results.append(check_ram_type(ram, board))
    if board and case:
        results.append(check_board_fits_case(board, case))
    if psu:
        others = [part for name, part in parts.items() if name != "PSU"]
        results.append(check_power_supply(psu, others))

    return [warning for warning in results if warning is not None]
