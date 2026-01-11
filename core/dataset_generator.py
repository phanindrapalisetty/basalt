from core.random_context import RandomContext
from core.generators.int_generator import IntGenerator

def generate_dataset(spec):
    rc = RandomContext(spec.get("seed"))

    # deterministic column order
    ordered_columns = sorted(spec.get("columns").keys())

    generators = {}
    rng=rc.rng

    for col_name in ordered_columns:
        col = spec.get("columns")[col_name]
        if col.get("type") == "int":
            generators[col_name] = IntGenerator(
                min_val=col.get("min"),
                max_val=col.get("max"),
                unique=col.get("unique"),
                rng=rng
            )

    rows = []

    for i in range(spec["rows"]):
        row = {}
        for col_name in ordered_columns:
            row[col_name] = generators[col_name].generate()
        rows.append(row)

    return rows
