# # tests/test_int_generator.py
# from core.random_context import RandomContext
# from core.generators.int_generator import IntGenerator


# def test_int_generator_deterministic_with_same_seed():
#     rc1 = RandomContext(seed=42)
#     rc2 = RandomContext(seed=42)

#     gen1 = IntGenerator(min_val=1, max_val=100, unique=False, rng=rc1.rng)
#     gen2 = IntGenerator(min_val=1, max_val=100, unique=False, rng=rc2.rng)

#     values1 = [gen1.generate() for _ in range(10)]
#     values2 = [gen2.generate() for _ in range(10)]

#     assert values1 == values2


# def test_int_generator_unique_values():
#     rc = RandomContext(seed=123)

#     gen = IntGenerator(min_val=1, max_val=10, unique=True, rng=rc.rng)

#     values = [gen.generate() for _ in range(10)]

#     assert len(values) == len(set(values))
#     assert all(1 <= v <= 10 for v in values)


# def test_int_generator_unique_deterministic():
#     rc1 = RandomContext(seed=99)
#     rc2 = RandomContext(seed=99)

#     gen1 = IntGenerator(min_val=100, max_val=200, unique=True, rng=rc1.rng)
#     gen2 = IntGenerator(min_val=100, max_val=200, unique=True, rng=rc2.rng)

#     values1 = [gen1.generate() for _ in range(20)]
#     values2 = [gen2.generate() for _ in range(20)]

#     assert values1 == values2
