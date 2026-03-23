import io


class ParquetFormatter:
    content_type = "application/octet-stream"
    extension = "parquet"

    def format(self, rows: list) -> bytes:
        try:
            import pyarrow as pa  # type: ignore[import-untyped]
            import pyarrow.parquet as pq  # type: ignore[import-untyped]
        except ImportError:
            raise RuntimeError(
                "Parquet support requires pyarrow. Install with: pip install pyarrow"
            )
        if not rows:
            return b""
        table = pa.Table.from_pylist(rows)
        buf = io.BytesIO()
        pq.write_table(table, buf)
        return buf.getvalue()
