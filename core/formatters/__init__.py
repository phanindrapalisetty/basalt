from core.formatters.json_formatter import JsonFormatter
from core.formatters.ndjson_formatter import NdjsonFormatter
from core.formatters.csv_formatter import CsvFormatter
from core.formatters.parquet_formatter import ParquetFormatter
from core.formatters.avro_formatter import AvroFormatter

_FORMATTERS = {
    "json": JsonFormatter,
    "ndjson": NdjsonFormatter,
    "csv": CsvFormatter,
    "parquet": ParquetFormatter,
    "avro": AvroFormatter,
}

SUPPORTED_FORMATS = list(_FORMATTERS.keys())


def get_formatter(fmt: str):
    cls = _FORMATTERS.get(fmt)
    if cls is None:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")
    return cls()
