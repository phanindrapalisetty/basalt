# core/generators/boolean_generator.py
import random

class BooleanGenerator:
    def __init__(self, rows: int, true_ratio: float, column_name: str, rc):
        self.rows = rows
        self.true_ratio = true_ratio

        # exact allocation (validator guarantees realizable)
        true_count = int(rows * true_ratio)
        false_count = rows - true_count

        self._sequence = [True] * true_count + [False] * false_count

        # IMPORTANT:
        # do NOT use the shared rc directly for shuffling, derive a local rc one: disturbs other generators
        
        local_rc = rc.sub_rng(column_name)
        local_rc.shuffle(self._sequence)

        self._index = 0

    def generate(self) -> bool:
        value = self._sequence[self._index]
        self._index += 1
        return value
