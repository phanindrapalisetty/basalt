from typing import List, Optional
import random
from core.random_context import RandomContext

class IntGenerator:
    def __init__(
        self,
        rows: int,
        min_val: int,
        max_val: int,
        unique: bool,
        null_ratio: float,
        column_name: str,
        rc: RandomContext, 
    ):

        self.rows = rows
        self.min_value = min_val
        self.max_value = max_val
        self.unique = unique
        self.null_ratio = null_ratio
        self.rc = rc
        self.column_name = column_name

        # IMPORTANT:
        # do NOT use the shared rc directly for shuffling, derive a local rc one: disturbs other generators
        
        self.local_rng = rc.sub_rng(column_name)
        self._sequence = self._build_sequence()
        self._index = 0
    
    def _build_sequence(self) -> List[Optional[int]]:
        null_count = self.rows * self.null_ratio
        value_count = self.rows - null_count

        if self.unique:
            values = self.local_rng.sample(
                range(self.min_value, self.max_value + 1),
                value_count
            )
        else:
            values = [
                self.local_rng.randint(self.min_value, self.max_value)
                for _ in range(value_count)
            ]

        seq: List[Optional[int]] = values + [None] * null_count
        self.local_rng.shuffle(seq)
        
        return seq 
    
    def generate(self) -> bool:
        value = self._sequence[self._index]
        self._index += 1
        return value
    
