import random
from core.random_context import RandomContext
from typing import Dict, Any, List, Optional


class DistributedStringGenerator:
    def __init__(
        self,
        rows: int,
        values: List[str],
        distribution: List[float],
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

        # IMPORTANT:
        # Same as int generator
        # do NOT use the shared rc directly for shuffling, derive a local rc one: disturbs other generators

        self.local_rng = rc.sub_rng(column_name)
        self._sequence = self._build_sequence()
        self._index = 0

    def _build_sequence(self) -> List[Optional[str]]:
        null_count = int(self.rows * self.null_ratio)

        _range = len(self.values)
        seq = []
        for i in range(0, _range):
            print(self.values[i])
            seq += [self.values[i]] * int(self.distribution[i] * self.rows)
        
        seq += [None] * null_count
        print(seq)

        self.local_rng.shuffle(seq)

        return seq
        
    def generate(self, row: dict | None = None) -> bool:
        value = self._sequence[self._index]
        self._index += 1
        return value

