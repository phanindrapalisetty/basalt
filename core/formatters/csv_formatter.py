import csv
import io


class CsvFormatter:
    content_type = "text/csv"
    extension = "csv"

    def format(self, rows: list) -> bytes:
        if not rows:
            return b""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue().encode()
