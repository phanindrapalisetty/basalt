# Changes

## Ratio-based (grouped) `map` values

Conditional `map` columns (see [usage.md](usage.md) / `conditional_generator.py`) previously only
supported a scalar per key — every row matching that key got the exact same value. This didn't
allow modelling something like: rows where `uom == "uom-1"` should split between `product-a` and
`product-b`, while keeping the ratio exact within that group.

`map` entries can now be either:
- a **scalar** (existing behavior) — every row with that key gets exactly that value
- a **grouped object** `{"values": [...], "distribution": [...]}` — rows with that key get one of
  `values`, sampled so the ratio is realized exactly within the rows belonging to that key

```json
"columns": {
    "uom": {
        "type": "string",
        "values": ["uom-1", "uom-2"],
        "distribution": [0.6, 0.4]
    },
    "product_name": {
        "type": "string",
        "depends_on": "uom",
        "map": {
            "uom-1": { "values": ["product-a", "product-b"], "distribution": [0.5, 0.5] },
            "uom-2": { "values": ["product-c"], "distribution": [1.0] }
        }
    }
}
```

With `rows: 10` and the `uom` distribution above, `uom-1` realizes to 6 rows and `uom-2` to 4 rows.
`product_name` then splits those 6 `uom-1` rows exactly 3/3 between `product-a`/`product-b`, and
sends all 4 `uom-2` rows to `product-c`.

### Constraints
- A `map`'s values must be **all scalars or all grouped objects** — mixing the two forms in the
  same `map` is rejected.
- Ratio-based `map` only works when `depends_on` points at a `string` column that itself has
  `values` + `distribution` (i.e. a `DistributedStringGenerator`-backed column). This is required
  so the exact row count per key is known before generation starts. Pointing `depends_on` at an
  `int`/`float`/`boolean`/`date` column, a `template`-derived string column, or another conditional
  (`map`/`ranges`) column raises a `SpecValidatorException` at validation time, before any rows are
  generated.
- Each grouped entry's `distribution` must exactly realize against that key's row count (e.g. a
  key with 7 rows can't be split 50/50) — same "must multiply out to an integer" rule used
  elsewhere in the spec (`null_ratio`, `true_ratio`, top-level `distribution`).

### Files touched
- `core/generators/conditional_generator.py` — `MapGenerator` builds a shuffled, exact-count
  sequence per grouped key and consumes it as matching rows are generated.
- `core/dataset_generator.py` — computes each key's group size from the `depends_on` column's
  spec before constructing `MapGenerator`.
- `core/spec_validator.py` — `_validate_grouped_map` validates the grouped form and rejects
  non-realizable ratios or an incompatible `depends_on` column.
