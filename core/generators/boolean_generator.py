import random
from core.random_context import RandomContext

class BooleanGenerator:
    def __init__(self, rows: int, true_ratio: float, null_ratio:float, column_name: str, rc: RandomContext):
        self.rows = rows
        self.true_ratio = true_ratio
        self.null_ratio = null_ratio
        self.column_name = column_name
        self.rc = rc

        # exact allocation (validator guarantees realizable)
        true_count = int(rows * true_ratio)
        null_count = int(rows * null_ratio)
        false_count = rows - true_count - null_count

        self._sequence = [True] * true_count + [False] * false_count + [None] * null_count

        # IMPORTANT:
        # do NOT use the shared rc directly for shuffling, derive a local rc one: disturbs other generators
        
        local_rng = rc.sub_rng(column_name)
        local_rng.shuffle(self._sequence)

        self._index = 0

    def generate(self, row: dict | None = None) -> bool:
        value = self._sequence[self._index]
        self._index += 1
        return value
