from core.random_context import RandomContext
from core.generators.int_generator import IntGenerator
from core.generators.boolean_generator import BooleanGenerator

def generate_dataset(spec):
    rc = RandomContext(spec.get("seed"))
    row_count = spec.get("rows")

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

        elif col.get("type") == "boolean":
            generators[col_name] = BooleanGenerator(
                rows=row_count,
                true_ratio=col.get("true_ratio"),
                column_name=col_name,
                rc=rc
            )
        
        else:
            raise ValueError(f"Unsupported column type: {col.get('type')}")

    rows = []

    for i in range(spec.get("rows")):
        row = {}
        for col_name in ordered_columns:
            row[col_name] = generators[col_name].generate()
        rows.append(row)

    return rows
