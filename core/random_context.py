import random

class RandomContext:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)