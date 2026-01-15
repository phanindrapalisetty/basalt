from core.random_context import RandomContext
from core.generators.int_generator import IntGenerator
from core.generators.boolean_generator import BooleanGenerator
from core.generators.float_generator import FloatGenerator
from core.spec_validator import SpecValidatorException
from core.generators.derived_generator import DerivedStringGenerator

def validate_dependencies(graph: dict[str, set[str]]) -> None:
    for col, deps in graph.items():
        if col in deps:
            raise SpecValidatorException(
                f"Column '{col}' cannot depend on itself"
            )

        for dep in deps:
            if dep not in graph:
                raise SpecValidatorException(
                    f"Column '{col}' depends on unknown column '{dep}'"
                )

def build_dependency_graph(columns: dict) -> dict[str, set[str]]:
    graph = {}

    for col_name, col_spec in columns.items():
        deps = col_spec.get("depends_on", [])
        if isinstance(deps, str):
            deps = [deps]

        graph[col_name] = set(deps)

    return graph


def topological_sort(graph: dict[str, set[str]]) -> list[str]:
    graph = {k: set(v) for k, v in graph.items()}
    result = []

    ready = sorted([k for k, v in graph.items() if not v])

    while ready:
        node = ready.pop(0)
        result.append(node)

        for other, deps in graph.items():
            if node in deps:
                deps.remove(node)
                if not deps:
                    ready.append(other)

        ready.sort()

    if len(result) != len(graph):
        raise SpecValidatorException("Circular dependency detected")

    return result


def generate_dataset(spec):
    rc = RandomContext(spec.get("seed"))
    row_count = spec.get("rows")

    # deterministic column order
    # ordered_columns = sorted(spec.get("columns").keys())
    graph = build_dependency_graph(spec["columns"])
    ordered_columns = topological_sort(graph)

    generators = {}

    for col_name in ordered_columns:
        col = spec.get("columns")[col_name]
        if col.get("type") == "int":
            generators[col_name] = IntGenerator(
                rows=row_count,
                min_val=col.get("min"),
                max_val=col.get("max"),
                unique=col.get("unique", False),
                null_ratio=col.get("null_ratio", 0.0),
                column_name=col_name,
                rc=rc,
            )

        elif col.get("type") == "boolean":
            generators[col_name] = BooleanGenerator(
                rows=row_count,
                true_ratio=col.get("true_ratio"),
                null_ratio=col.get("null_ratio", 0.0),
                column_name=col_name,
                rc=rc
            )
        
        elif col.get("type") == "float":
            generators[col_name] = FloatGenerator(
                rows=row_count,
                min_val=col.get("min"),
                max_val=col.get("max"),
                rounding=col.get("rounding", 6),
                null_ratio=col.get("null_ratio", 0.0),
                column_name=col_name,
                rc=rc,
            )
        
        elif col.get("type") == "string" and col.get("depends_on") is not None:
            generators[col_name] = DerivedStringGenerator(
                depends_on=col.get("depends_on"),
                template=col.get("template"),
                
            )
        
        else:
            raise ValueError(f"Unsupported column type: {col.get('type')}")

    rows = []

    for i in range(spec.get("rows")):
        row = {}
        for col_name in ordered_columns:
            row[col_name] = generators[col_name].generate(row)
        rows.append(row)

    return rows
