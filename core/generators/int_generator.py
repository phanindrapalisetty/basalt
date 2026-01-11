class IntGenerator:
    def __init__(self, min_val: int, max_val: int, unique: bool, rng):
        self.min = min_val
        self.max = max_val
        self.unique = unique
        self.rng = rng

        self._used = set() if unique else None

    def generate(self) -> int:
        if not self.unique:
            return self.rng.randint(self.min, self.max)

        # unique = True
        while True:
            value = self.rng.randint(self.min, self.max)
            if value not in self._used:
                self._used.add(value)
                return value
