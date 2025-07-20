def safe_str(cell):
    return str(cell).strip() if cell is not None else ""


def subtract_vectors(v1, v2):
    """Subtract one vector from another."""
    return [a - b for a, b in zip(v1, v2)] if v1 and v2 and len(v1) == len(v2) else v1
