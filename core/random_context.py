import random

class RandomContext:
    def __init__(self, seed: int):
        self.seed = seed
        self.rng = random.Random(seed)

    def sub_rng(self, namespace: str):
        """
        A deterministic, isolated RNG for a specific purpose without consuming the main RNG.
        For example, shuffling in boolean and string generators.
        """
        derived_seed = hash((self.seed, namespace)) & 0xFFFFFFFF
        return random.Random(derived_seed)