import math
from core.random_context import RandomContext
from typing import List, Optional


def _weights_to_counts(weights: List[int], non_null_rows: int) -> List[int]:
    """Convert integer weights to exact row counts using the Largest Remainder Method.

    Guarantees sum(counts) == non_null_rows regardless of rounding.
    """
    total_weight = sum(weights)
    ideals = [w / total_weight * non_null_rows for w in weights]
    floors = [math.floor(v) for v in ideals]
    remainders = [(ideals[i] - floors[i], i) for i in range(len(weights))]
    shortage = non_null_rows - sum(floors)
    # Distribute the shortage to the indices with the largest remainders
    remainders.sort(key=lambda x: -x[0])
    for k in range(shortage):
        floors[remainders[k][1]] += 1
    return floors


class DistributedStringGenerator:
    def __init__(
        self,
        rows: int,
        values: List[str],
        distribution,
        column_name: str,
        null_ratio: float,
        rc: RandomContext,
    ):
        self.rows = rows
        self.values = values
        self.distribution = distribution
        self.column_name = column_name
        self.null_ratio = null_ratio
        self.rc = rc

        # IMPORTANT: derive a local sub-rng to avoid disturbing other generators
        self.local_rng = rc.sub_rng(column_name)
        self._sequence = self._build_sequence()
        self._index = 0

    def _build_sequence(self) -> List[Optional[str]]:
        null_count = int(self.rows * self.null_ratio)
        non_null_rows = self.rows - null_count

        all_int = all(isinstance(p, int) and not isinstance(p, bool) for p in self.distribution)

        if all_int:
            counts = _weights_to_counts(self.distribution, non_null_rows)
        else:
            # Ratio mode: each ratio × rows gives exact integer count (validated upstream)
            counts = [int(p * self.rows) for p in self.distribution]

        seq: List[Optional[str]] = []
        for value, count in zip(self.values, counts):
            seq += [value] * count

        seq += [None] * null_count
        self.local_rng.shuffle(seq)
        return seq

    def generate(self, row: dict | None = None) -> Optional[str]:
        value = self._sequence[self._index]
        self._index += 1
        return value


class DerivedStringGenerator:
    def __init__(self, depends_on: str, template: str):
        self.depends_on = depends_on
        self.template = template

    def generate(self, row: dict):
        value = row[self.depends_on]
        return None if value is None else self.template.format(value=value)
