class SequentialIntGenerator:
    def __init__(self, rows: int, start: int, step: int):
        self._values = [start + i * step for i in range(rows)]
        self._index = 0

    def generate(self, _row: dict):
        value = self._values[self._index]
        self._index += 1
        return value
