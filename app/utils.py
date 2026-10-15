def require_id(value: int | None) -> int:
    """Rows have `id = None` until they are saved; call this once a row is in the database."""
    if value is None:
        raise RuntimeError("Row has no id yet - was it saved?")
    return value
