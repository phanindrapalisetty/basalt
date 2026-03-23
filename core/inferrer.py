import re


_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
_PHONE_RE = re.compile(r"^\+?\d[\d\s\-().]{6,}$")


def _max_decimals(values):
    max_d = 0
    for v in values:
        if v is not None:
            s = str(v)
            if "." in s:
                max_d = max(max_d, len(s.split(".")[1]))
    return max_d


def _infer_column(values: list) -> dict:
    non_null = [v for v in values if v is not None]
    null_count = len(values) - len(non_null)
    null_ratio = null_count / len(values) if values else 0.0

    base: dict = {}
    if null_ratio > 0:
        base["null_ratio"] = round(null_ratio, 4)

    if not non_null:
        return {**base, "type": "string", "values": [], "distribution": []}

    # bool (check before int — Python bool is subclass of int)
    if all(isinstance(v, bool) for v in non_null):
        true_ratio = sum(1 for v in non_null if v) / len(non_null)
        return {**base, "type": "boolean", "true_ratio": round(true_ratio, 4)}

    # int
    if all(isinstance(v, int) for v in non_null):
        return {**base, "type": "int", "min": min(non_null), "max": max(non_null)}

    # float
    if all(isinstance(v, float) for v in non_null):
        return {
            **base,
            "type": "float",
            "min": float(min(non_null)),
            "max": float(max(non_null)),
            "rounding": _max_decimals(non_null),
        }

    # string patterns
    if all(isinstance(v, str) for v in non_null):
        if all(_UUID_RE.match(v) for v in non_null):
            return {**base, "type": "uuid"}
        if all(_DATETIME_RE.match(v) for v in non_null):
            return {**base, "type": "timestamp", "start": min(non_null), "end": max(non_null)}
        if all(_DATE_RE.match(v) for v in non_null):
            return {**base, "type": "date", "start_date": min(non_null), "end_date": max(non_null)}
        if all(_EMAIL_RE.match(v) for v in non_null):
            return {**base, "type": "email", "domains": list({v.split("@")[1] for v in non_null})}
        if all(_PHONE_RE.match(v) for v in non_null):
            return {**base, "type": "phone"}

        unique_vals = list(dict.fromkeys(non_null))  # preserve order, deduplicate
        if len(unique_vals) <= 20:
            total = len(values)
            distribution = [round(non_null.count(v) / total, 4) for v in unique_vals]
            return {**base, "type": "string", "values": unique_vals, "distribution": distribution}

        # high-cardinality — fall back to sample
        return {**base, "type": "string", "values": unique_vals[:20], "distribution": [round(1 / min(len(unique_vals), 20), 4)] * min(len(unique_vals), 20)}

    return {**base, "type": "string", "values": [], "distribution": []}


def infer_spec(rows: list, seed: int = 42) -> dict:
    if not rows:
        return {"rows": 10, "seed": seed, "columns": {}}

    columns = {}
    for col_name in rows[0].keys():
        values = [row.get(col_name) for row in rows]
        columns[col_name] = _infer_column(values)

    return {"rows": len(rows), "seed": seed, "columns": columns}
