from typing import List, Optional
import random

class FloatGenerator:
    def __init__(
        self,
        rows: int,
        min_val: int,
        max_val: int,
        rounding: int,
        null_ratio: float,
        column_name: str,
        rc, 
        
    ):

        self.rows = rows
        self.min_value = min_val
        self.max_value = max_val
        self.rounding = rounding
        self.null_ratio = null_ratio
        self.rc = rc
        self.column_name = column_name

        # IMPORTANT:
        # do NOT use the shared rc directly for shuffling, derive a local rc one: disturbs other generators
        
        self.local_rng = rc.sub_rng(column_name)
        self._sequence = self._build_sequence()
        self._index = 0
    
    def _build_sequence(self) -> List[Optional[float]]:
        null_count = int(self.rows * self.null_ratio)
        value_count = self.rows - null_count

        values = [
            round(self.local_rng.uniform(self.min_value, self.max_value), self.rounding)
            for _ in range(value_count)
        ]

        seq: List[Optional[float]] = values + [None] * null_count
        self.local_rng.shuffle(seq)
        
        return seq 
    
    def generate(self, row: dict | None = None) -> bool:
        value = self._sequence[self._index]
        self._index += 1
        return value
    
