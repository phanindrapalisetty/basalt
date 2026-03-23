import json


class JsonFormatter:
    content_type = "application/json"
    extension = "json"

    def format(self, rows: list) -> bytes:
        return json.dumps(rows).encode()
