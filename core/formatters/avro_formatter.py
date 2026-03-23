import io


def _infer_avro_schema(rows: list) -> dict:
    if not rows:
        return {"type": "record", "name": "Row", "fields": []}
    sample = rows[0]
    type_map = {int: "long", float: "double", bool: "boolean", str: "string"}
    fields = []
    for key, val in sample.items():
        avro_type = type_map.get(type(val), "string")
        # check for nulls across all rows
        has_null = any(r.get(key) is None for r in rows)
        fields.append({
            "name": key,
            "type": ["null", avro_type] if has_null else avro_type,
        })
    return {"type": "record", "name": "Row", "fields": fields}


class AvroFormatter:
    content_type = "application/avro"
    extension = "avro"

    def format(self, rows: list) -> bytes:
        try:
            import fastavro  # type: ignore[import-untyped]
        except ImportError:
            raise RuntimeError(
                "Avro support requires fastavro. Install with: pip install fastavro"
            )
        schema = _infer_avro_schema(rows)
        parsed = fastavro.parse_schema(schema)
        buf = io.BytesIO()
        fastavro.writer(buf, parsed, rows)
        return buf.getvalue()
