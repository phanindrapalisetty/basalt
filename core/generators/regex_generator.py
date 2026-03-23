import rstr  # type: ignore[import-untyped]


class RegexGenerator:
    def __init__(self, rows: int, pattern: str, null_ratio: float, column_name: str, rc):
        local_rng = rc.sub_rng(column_name)
        rng = rstr.Rstr()
        rng.random = local_rng

        null_count = int(rows * null_ratio)
        value_count = rows - null_count

        values = [rng.xeger(pattern) for _ in range(value_count)]
        values += [None] * null_count
        local_rng.shuffle(values)

        self._values = values
        self._index = 0

    def generate(self, _row: dict):
        value = self._values[self._index]
        self._index += 1
        return value
