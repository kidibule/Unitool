def format_int_with_dots(value) -> str:
    """Format an integer-like value with '.' as thousands separator.

    Accepts int or strings like '1000000', '1 000 000', '1,000,000' or '1.000.000'.
    Returns an empty string for None or empty-like values.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if s in ("", "None"):
        return ""
    # Remove common thousands separators and spaces to parse integer
    cleaned = s.replace(" ", "").replace(".", "").replace(",", "")
    try:
        n = int(cleaned)
    except Exception:
        return s
    # Use Python formatting then swap comma->dot
    return f"{n:,}".replace(",", ".")
