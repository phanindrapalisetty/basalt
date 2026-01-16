from datetime import datetime, timedelta, date
from core.random_context import RandomContext
from typing import List, Optional, Any

class DateGenerator:
    def __init__(self, rows: int, start_date:str, end_date:str, column_name:str, null_ratio: float, rc: RandomContext):
        self.rows = rows
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        self.column_name = column_name
        self.null_ratio = null_ratio
        self.rc = rc

        # IMPORTANT:
        # do NOT use the shared rc directly for shuffling, derive a local rc one: disturbs other generators

        self._delta = (self.end_date - self.start_date).days
        print(self._delta)

        self.local_rng = rc.sub_rng(column_name)
        self._sequence = self._build_sequence()
        self._index = 0

    def _build_sequence(self) -> List[Optional[int]]:
        null_count = int(self.rows * self.null_ratio)
        value_count = self.rows - null_count

        offset = [self.local_rng.randint(0, self._delta) for _ in range(value_count)]

        dates = [self.start_date + timedelta(days=offset) for offset in offset]

        seq = dates + [None] * null_count
        self.local_rng.shuffle(seq)

        return seq

    def generate(self, row: dict | None = None) -> bool:
        value = self._sequence[self._index].isoformat()
        self._index += 1
        return value