class FloatGenerator:
    def __init__(self, min_val: float, max_val: float, unique: bool, rng):
        self.min = min_val
        self.max = max_val
        self.unique = unique
        self.rng = rng

        self._used = set() if unique else None

    def generate(self) -> int:
        if not self.unique:
            return round(self.rng.randint(self.min, self.max), 6)

        # unique = True
        while True:
            value = self.rng.randint(self.min, self.max)
            if value not in self._used:
                self._used.add(value)
                return value