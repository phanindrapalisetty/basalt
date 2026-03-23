import json


class NdjsonFormatter:
    content_type = "application/x-ndjson"
    extension = "ndjson"

    def format(self, rows: list) -> bytes:
        return b"\n".join(json.dumps(row).encode() for row in rows)
