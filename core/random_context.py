import random
import hashlib


class RandomContext:
    def __init__(self, seed: int):
        self.seed = seed
        self.rng = random.Random(seed)

    def sub_rng(self, namespace: str):
        """
        A deterministic, isolated RNG for a specific purpose without consuming the main RNG.
        For example, shuffling in boolean and string generators.
        """
        key = f"{self.seed}:{namespace}".encode()
        derived_seed = int(hashlib.sha256(key).hexdigest(), 16) % (2**32)
        return random.Random(derived_seed)
