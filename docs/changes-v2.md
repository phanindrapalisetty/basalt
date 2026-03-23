# Basalt v2 — Changes & Smoke Tests

All changes are implemented as independent feature branches off `main`. Each branch is self-contained and can be reviewed/merged separately.

---

## Branch 1 — `feature/v2-versioning-rate-limit`

### Changes

**`api/routers/v1.py`** _(new)_
- All endpoints moved under `/v1` prefix via `FastAPI APIRouter`
- Rate limiting applied per-endpoint via `slowapi` decorators

**`api/rate_limit.py`** _(new)_
- `slowapi` `Limiter` with `get_remote_address` key function
- Configurable via env vars:
  - `RATE_LIMIT_ENABLED` (default `true`)
  - `RATE_LIMIT_PER_MINUTE` (default `60`)

**`api/main.py`** _(updated)_
- Mounts the `/v1` router
- Registers `RateLimitExceeded` exception handler (returns 429)
- Adds backwards-compat redirect: `POST /generate → POST /v1/generate` (HTTP 308 — preserves method and body)

**`requirements.txt`** _(pinned)_
```
fastapi==0.115.6
uvicorn==0.34.0
mangum==0.19.0
slowapi==0.1.9
rstr==3.2.2
fastavro==1.9.7
pyarrow==18.1.0
```

**`requirements-dev.txt`** _(new)_
```
requests==2.32.3
pytest==8.3.4
```

### Smoke Tests

```python
# App imports without error
from api.main import app  # → OK

# Existing tests (all pass)
pytest tests/ -q  # → 14 passed
```

---

## Branch 2 — `feature/v2-limits`

### Changes

**`core/spec_validator.py`** _(updated)_
- `MAX_ROWS` raised from `1000` to `5000`, overridable via `MAX_ROWS` env var
- `MAX_CELLS = rows × columns` cap added, default `1,000,000`, overridable via `MAX_CELLS` env var
- Cell count check added after columns validation — returns 422 with descriptive message

```python
import os
MAX_ROWS = int(os.getenv("MAX_ROWS", 5000))
MAX_CELLS = int(os.getenv("MAX_CELLS", 1_000_000))

# Inside _validate_top_level:
total_cells = rows * len(columns)
if total_cells > MAX_CELLS:
    raise SpecValidatorException(
        f"Total cells (rows × columns) cannot exceed {MAX_CELLS:,}. Got {total_cells:,}."
    )
```

### Smoke Tests

```python
# rows=5000 (new limit) — accepted
SpecValidator.validate({"rows": 5000, "seed": 1, "columns": {"x": {"type": "int", "min": 1, "max": 10}}})
# → OK

# rows=5001 — rejected
SpecValidator.validate({"rows": 5001, ...})
# → SpecValidatorException: 'rows' must be an integer between 1 and 5000

# 5000 rows × 201 columns = 1,005,000 cells — rejected
# → SpecValidatorException: Total cells (rows × columns) cannot exceed 1,000,000. Got 1,005,000.

pytest tests/ -q  # → 14 passed
```

---

## Branch 3 — `feature/v2-sequential-regex`

### Changes

**`core/generators/sequential_int_generator.py`** _(new)_
- Generates integers starting at `start` incrementing by `step`
- Fully deterministic — no RNG involved
- Incompatible with `null_ratio > 0` (validated upstream)

```python
class SequentialIntGenerator:
    def __init__(self, rows, start, step):
        self._values = [start + i * step for i in range(rows)]
```

**`core/generators/regex_generator.py`** _(new)_
- Uses `rstr.xeger(pattern)` to generate strings matching the given regex
- Seeded via `rc.sub_rng(column_name)` for determinism
- Supports `null_ratio`

**`core/spec_validator.py`** _(updated)_
- `"regex"` added to `ALLOWED_TYPES`
- `_validate_int_column`: detects `sequential: true`, validates `start` (int) and `step` (non-zero int), rejects `null_ratio > 0` for sequential columns, returns early (skips min/max checks)
- `_validate_regex_column`: checks `pattern` is a non-empty string and compiles via `re.compile` to catch invalid regex early

**`core/dataset_generator.py`** _(updated)_
- Adds `SequentialIntGenerator` and `RegexGenerator` imports
- Handles `int` + `sequential: true` and `regex` type in the generator dispatch chain

### Smoke Tests

```python
# Sequential int — start=10, step=5
spec = {"seed": 42, "rows": 5, "columns": {"id": {"type": "int", "sequential": True, "start": 10, "step": 5}}}
rows = generate_dataset(spec)
print([r["id"] for r in rows])
# → [10, 15, 20, 25, 30]

# Regex
spec2 = {"seed": 42, "rows": 3, "columns": {"code": {"type": "regex", "pattern": "[A-Z]{3}-[0-9]{4}"}}}
rows2 = generate_dataset(spec2)
print([r["code"] for r in rows2])
# → ['WGF-1734', 'BUQ-2105', 'YCA-7275']  (deterministic)

pytest tests/ -q  # → 14 passed
```

---

## Branch 4 — `feature/v2-conditional`

### Changes

**`core/generators/conditional_generator.py`** _(new)_

`MapGenerator` — value lookup:
- `map` dict: maps source column value → output value
- Falls back to `default` if key not found or source is null

`RangeGenerator` — numeric range lookup:
- `ranges` list: each entry has `min` (inclusive, null = unbounded), `max` (inclusive, null = unbounded), `then`
- Falls back to `default` if no range matches

**`core/spec_validator.py`** _(updated)_
- `_validate_conditional_column`: validates `depends_on` is present; checks `map`/`ranges` cannot both be specified; validates map value type homogeneity; validates each range entry has `then` and numeric `min`/`max`
- `_validate_column`: detects `map` or `ranges` key → dispatches to `_validate_conditional_column` and returns early (skips normal type checks)

**`core/dataset_generator.py`** _(updated)_
- `map`/`ranges` keys checked first in the `elif` chain before type-based dispatch

### Smoke Tests

```python
# Map: country → currency
spec = {
    "seed": 1, "rows": 4,
    "columns": {
        "country": {"type": "string", "values": ["US","UK","CA","DE"], "distribution": [0.25,0.25,0.25,0.25]},
        "currency": {"type": "string", "depends_on": "country", "map": {"US":"USD","UK":"GBP","CA":"CAD"}, "default": "EUR"}
    }
}
# → [('US','USD'), ('DE','EUR'), ('CA','CAD'), ('UK','GBP')]

# Ranges: age → group
spec2 = {
    "seed": 1, "rows": 5,
    "columns": {
        "age": {"type": "int", "min": 5, "max": 80},
        "group": {"type": "string", "depends_on": "age", "ranges": [
            {"min": 0, "max": 17, "then": "minor"},
            {"min": 18, "max": 64, "then": "adult"},
            {"min": 65, "max": None, "then": "senior"}
        ], "default": "unknown"}
    }
}
# → [(48,'adult'), (40,'adult'), (24,'adult'), (73,'senior'), (45,'adult')]

pytest tests/ -q  # → 14 passed
```

---

## Branch 5 — `feature/v2-output-formats`

### Changes

**`core/formatters/`** _(new directory)_

| File | Class | Content-Type | Notes |
|---|---|---|---|
| `json_formatter.py` | `JsonFormatter` | `application/json` | Returns raw list as bytes |
| `ndjson_formatter.py` | `NdjsonFormatter` | `application/x-ndjson` | One JSON object per line |
| `csv_formatter.py` | `CsvFormatter` | `text/csv` | Uses stdlib `csv`, handles nulls as empty string |
| `parquet_formatter.py` | `ParquetFormatter` | `application/octet-stream` | `pyarrow` imported lazily — raises `RuntimeError` if not installed |
| `avro_formatter.py` | `AvroFormatter` | `application/octet-stream` | `fastavro`, schema inferred from first row; nullable fields use `["null", type]` union |
| `__init__.py` | `get_formatter(fmt)` | — | Factory; raises `ValueError` for unknown format |

**`api/main.py`** _(updated)_
- `POST /generate` accepts `?format=` query param (default `json`)
- JSON format preserves existing `{"data": [...]}` envelope (backwards compat)
- All other formats return a binary file download with `Content-Disposition: attachment`
- `ValueError` from unknown format returns 422

### Smoke Tests

```python
from core.formatters import get_formatter

rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": None}]
for fmt in ["json", "ndjson", "csv", "parquet", "avro"]:
    data = get_formatter(fmt).format(rows)
    print(f"{fmt}: {len(data)} bytes OK")
# json:    53 bytes OK
# ndjson:  50 bytes OK
# csv:     22 bytes OK
# parquet: 708 bytes OK
# avro:    203 bytes OK

pytest tests/ -q  # → 14 passed
```

---

## Branch 6 — `feature/v2-validate-infer`

### Changes

**`core/inferrer.py`** _(new)_

`infer_spec(rows, seed)` — inspects a list of dicts and returns a Basalt spec:

| Detected type | Condition |
|---|---|
| `boolean` | All non-null values are Python `bool` |
| `int` | All non-null values are Python `int` |
| `float` | All non-null values are Python `float` |
| `uuid` | All match `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `timestamp` | All match ISO datetime prefix |
| `date` | All match `YYYY-MM-DD` |
| `email` | All match `x@x.x` |
| `phone` | All match phone-like pattern |
| `string` (enum) | ≤ 20 unique string values → `values` + `distribution` |
| `string` (high-card) | > 20 unique values → first 20 as sample |

Detection order: date/datetime checked **before** phone to prevent false matches (e.g. `2024-01-15` matches phone regex otherwise).

`null_ratio` inferred from proportion of nulls per column.

**`api/main.py`** _(updated)_
- `POST /validate` — runs `SpecValidator.validate`, returns `{"valid": true}` or `{"valid": false, "error": "..."}` (422)
- `POST /infer` — accepts `{"rows": [...], "seed": 42}`, returns `{"spec": {...}}`

### Smoke Tests

```python
from core.inferrer import infer_spec

rows = [
    {"id": 1, "name": "Alice", "score": 0.95, "active": True,  "joined": "2024-01-15"},
    {"id": 2, "name": "Bob",   "score": 0.72, "active": False, "joined": "2024-03-10"},
    {"id": 3, "name": None,    "score": 0.88, "active": True,  "joined": "2024-06-01"},
]
spec = infer_spec(rows, seed=7)
# id     → {type: int,     min: 1,    max: 3}
# name   → {null_ratio: 0.3333, type: string, values: ["Alice","Bob"], distribution: [0.3333, 0.3333]}
# score  → {type: float,   min: 0.72, max: 0.95, rounding: 2}
# active → {type: boolean, true_ratio: 0.6667}
# joined → {type: date,    start_date: "2024-01-15", end_date: "2024-06-01"}

pytest tests/ -q  # → 14 passed
```

---

## Branch 7 — `feature/v2-ui`

### Changes

**`ui/api_client.py`** _(new)_
- Thin `requests` wrapper; reads `BASALT_API_URL` env var (default `http://localhost:8000`)
- Functions: `generate(spec, fmt)`, `validate(spec)`, `infer(rows, seed)`, `health()`

**`ui/app.py`** _(new — Streamlit)_

| Section | Description |
|---|---|
| Sidebar | API URL, seed, row count, output format selector, live API health indicator |
| Builder tab | Per-column expanders with type-specific fields (min/max, values/distribution, pattern, etc.), live spec JSON preview, spec download, Validate + Generate buttons, multi-format download |
| Paste Spec tab | Raw JSON textarea to import an existing spec into the Builder |

Run with:
```bash
BASALT_API_URL=http://localhost:8000 streamlit run ui/app.py
```

**`requirements-ui.txt`** _(new)_
```
streamlit==1.41.1
requests==2.32.3
```

### Smoke Tests

```python
# Syntax check
import ast
ast.parse(open("ui/app.py").read())  # → OK

# api_client imports
from ui.api_client import health, generate, validate, infer  # → OK

pytest tests/ -q  # → 14 passed
```

---

## Branch 8 — `feature/v2-weighted-distribution`

### Changes

**`core/generators/string_generator.py`** _(updated)_

Added `_weights_to_counts(weights, non_null_rows)` — converts integer weights to exact row counts using the **Largest Remainder Method**, guaranteeing `sum(counts) == non_null_rows` for any row count.

```python
def _weights_to_counts(weights, non_null_rows):
    total_weight = sum(weights)
    ideals = [w / total_weight * non_null_rows for w in weights]
    floors = [math.floor(v) for v in ideals]
    remainders = sorted(enumerate(ideals), key=lambda x: -(x[1] - floors[x[0]]))
    shortage = non_null_rows - sum(floors)
    for k in range(shortage):
        floors[remainders[k][0]] += 1
    return floors
```

`DistributedStringGenerator._build_sequence` — detects mode from `distribution` element types:
- All `int` → weights mode (new)
- All `float` → ratio mode (existing, unchanged)

**`core/spec_validator.py`** _(updated)_

`_validate_distribution` rewritten to handle both modes:

| Distribution | Mode | Validation |
|---|---|---|
| `[0.3, 0.7]` (floats) | Ratio | Each `p × rows` must be an exact integer; sum must account for all rows |
| `[1, 2, 7]` (ints) | Weight | All values must be positive integers; normalization done at generation time |
| `[1, 0.5]` (mixed) | — | Rejected: "must be all floats or all ints, not mixed" |

### Smoke Tests

```python
from core.spec_validator import SpecValidator
from core.dataset_generator import generate_dataset
from collections import Counter

# Weights [1, 2, 7] on 10 rows
spec = {"seed": 42, "rows": 10, "columns": {
    "tier": {"type": "string", "values": ["gold","silver","bronze"], "distribution": [1, 2, 7]}
}}
SpecValidator.validate(spec)
rows = generate_dataset(spec)
Counter(r["tier"] for r in rows)
# → {'bronze': 7, 'silver': 2, 'gold': 1}  ✓ proportional, exact

# Weights + null_ratio=0.2 on 20 rows
spec2 = {"seed": 42, "rows": 20, "columns": {
    "status": {"type": "string", "values": ["A","B"], "distribution": [3, 1], "null_ratio": 0.2}
}}
# → {'A': 12, 'B': 4, None: 4}  ✓ 16 non-null split 3:1, 4 nulls

# Ratios still work unchanged
spec3 = {"seed": 42, "rows": 10, "columns": {
    "flag": {"type": "string", "values": ["yes","no"], "distribution": [0.3, 0.7]}
}}
# → {'no': 7, 'yes': 3}  ✓

# Validation errors
SpecValidator.validate({..., "distribution": [1, 0.5]})   # → "must be all floats or all ints, not mixed"
SpecValidator.validate({..., "distribution": [-1, 3]})    # → "weights must be positive integers"
SpecValidator.validate({..., "distribution": [0.33, 0.67]})  # → "0.33 cannot be realized with 10 rows"

pytest tests/ -q  # → 14 passed
```

---

## Summary Table

| Branch | Files Changed | Feature |
|---|---|---|
| `feature/v2-versioning-rate-limit` | `api/main.py`, `api/routers/v1.py`, `api/rate_limit.py`, `requirements.txt`, `requirements-dev.txt` | `/v1` API prefix, 308 redirect, slowapi rate limiter, pinned deps |
| `feature/v2-limits` | `core/spec_validator.py` | MAX_ROWS=5000, MAX_CELLS=1M (env-var configurable) |
| `feature/v2-sequential-regex` | `core/generators/sequential_int_generator.py`, `core/generators/regex_generator.py`, `core/spec_validator.py`, `core/dataset_generator.py` | Sequential int (start/step), regex generator (rstr) |
| `feature/v2-conditional` | `core/generators/conditional_generator.py`, `core/spec_validator.py`, `core/dataset_generator.py` | Map (value lookup) and ranges (numeric bounds) conditional columns |
| `feature/v2-output-formats` | `core/formatters/` (5 files + `__init__.py`), `api/main.py` | JSON, NDJSON, CSV, Parquet, Avro via `?format=` param |
| `feature/v2-validate-infer` | `core/inferrer.py`, `api/main.py` | `POST /validate`, `POST /infer`, type inference from sample data |
| `feature/v2-ui` | `ui/app.py`, `ui/api_client.py`, `requirements-ui.txt` | Streamlit spec builder UI |
| `feature/v2-weighted-distribution` | `core/generators/string_generator.py`, `core/spec_validator.py` | Integer weights alongside float ratios for string distribution |
