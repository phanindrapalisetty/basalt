# Basalt v2 — Feature Plan

## Implementation Order
Each item is ordered by dependency — versioning first since it touches all endpoints.

---

## 1. API Versioning

**Approach:** FastAPI `APIRouter` with `/v1` prefix. All new and existing endpoints move under `/v1`. Old unversioned paths (`/generate`, `/generate/multi`) remain as redirect aliases for backwards compatibility.

**Files:**
- `api/routers/v1.py` — new file, all endpoints move here
- `api/main.py` — mounts router, keeps `/health` at root, adds backward-compat redirects

**Endpoint map after versioning:**
```
GET  /health              →  unchanged (infra probe, no version)
POST /v1/generate         →  was /generate
POST /v1/generate/multi   →  was /generate/multi
POST /v1/validate         →  new
POST /v1/infer            →  new
GET  /v1/formats          →  new (lists supported output formats)
```

**Backward compat:**
```python
@app.post("/generate")
async def generate_compat(payload: dict):
    return RedirectResponse(url="/v1/generate", status_code=308)
```

---

## 2. Pin requirements.txt

**Current (unpinned):**
```
fastapi
uvicorn
requests
pytest
mangum
```

**Pinned — add new dependencies too:**
```
fastapi==0.115.6
uvicorn==0.34.0
requests==2.32.3
pytest==8.3.4
mangum==0.19.0
slowapi==0.1.9
rstr==3.2.2
fastavro==1.9.7
pyarrow==18.1.0
```

**Note:** `requests` is only used in tests — move to a separate `requirements-dev.txt`. `pyarrow` is large (~40MB); add a comment noting it can be excluded for lightweight deployments that don't need Parquet.

---

## 3. Rate Limiter

**Library:** `slowapi` — the standard FastAPI rate limiter, wraps `limits`.

**Strategy:** Per-IP, configurable via env vars. No API keys required (open source friendly).

**Env vars:**
```
RATE_LIMIT_PER_MINUTE=60      # default: 60 requests/min per IP
RATE_LIMIT_ENABLED=true       # default: true (set false for local dev)
```

**Files:**
- `api/rate_limit.py` — new file, creates `Limiter` instance, reads env vars
- `api/routers/v1.py` — applies `@limiter.limit(...)` decorator to each endpoint

**Behaviour:**
- Exceeding limit → HTTP 429 with `Retry-After` header
- `/health` is exempt from rate limiting
- `/v1/validate` has a higher limit (validation is cheap): `RATE_LIMIT_VALIDATE_PER_MINUTE=200`

---

## 4. Row Limit + Cell Limit

**New constants (env-var backed):**
```python
MAX_ROWS      = int(os.getenv("MAX_ROWS", 5000))
MAX_CELLS     = int(os.getenv("MAX_CELLS", 1_000_000))
```

**Cell check:** `rows × len(columns) > MAX_CELLS` → 422

**Files:** `core/spec_validator.py` — update `_validate_top_level` and `validate_multi`

**Error messages:**
```
"'rows' must be an integer between 1 and 5000"
"Total cells (rows × columns) cannot exceed 1,000,000. Got 1,200,000."
```

**For `/generate/multi`:** total cells = sum of `(dataset.rows × len(dataset.columns))` across all datasets.

---

## 5. Sequential Int Generator

**Spec:**
```json
{ "type": "int", "sequential": true, "start": 1, "step": 1 }
```

**Rules:**
- `start`: required int (default: 1)
- `step`: optional int, non-zero (default: 1), can be negative for descending
- `sequential: true` is incompatible with `null_ratio > 0` (sequence would have gaps — raise 422)
- `sequential: true` is incompatible with `unique: false` (sequential is always unique by definition — warn but allow, treat as unique)
- No `min`/`max` required when `sequential: true`

**Output:** row 0 → `start`, row 1 → `start + step`, row 2 → `start + 2×step`, ...

**Files:**
- `core/generators/sequential_int_generator.py` — new file (no RNG needed, pure arithmetic)
- `core/spec_validator.py` — add sequential checks in `_validate_int_column`
- `core/dataset_generator.py` — detect `sequential: true` and instantiate `SequentialIntGenerator`

**No RNG used** — output is fully deterministic without a seed.

---

## 6. Regex Generator

**Spec:**
```json
{ "type": "regex", "pattern": "[A-Z]{3}-\\d{4}", "null_ratio": 0.1 }
```

**Library:** `rstr` — generates random strings matching a regex.

**Determinism:** `rstr.Rstr` uses Python's `random` module internally. Seed it via our `sub_rng`:
```python
local_rng = rc.sub_rng(column_name)
rng = rstr.Rstr()
rng.random = local_rng   # inject our seeded random instance
values = [rng.xeger(pattern) for _ in range(value_count)]
```

**Validation:**
- `pattern` is required, must be a non-empty string
- Validate with `re.compile(pattern)` — raise 422 if invalid regex
- Warn (but allow) overly broad patterns like `.*` that may produce very long strings

**Files:**
- `core/generators/regex_generator.py`
- `core/spec_validator.py` — add `_validate_regex_column`
- `core/dataset_generator.py` — register `RegexGenerator`

---

## 7. Conditional Generation

Two modes, both extend the `depends_on` pattern:

### Mode A — `map` (value lookup)
```json
{
  "type": "string",
  "depends_on": "country",
  "map": { "US": "USD", "UK": "GBP", "CA": "CAD" },
  "default": "USD"
}
```
- `map`: dict of `dependency_value → output_value`
- `default`: value to use when dependency value is not in map (required if map doesn't cover all values)
- Output type matches values in `map` (all must be same type)

### Mode B — `ranges` (numeric range lookup)
```json
{
  "type": "string",
  "depends_on": "age",
  "ranges": [
    { "min": 0,  "max": 17, "then": "minor" },
    { "min": 18, "max": 64, "then": "adult" },
    { "min": 65, "max": null, "then": "senior" }
  ],
  "default": "unknown"
}
```
- `min`/`max` are inclusive bounds; `null` means unbounded
- First matching range wins
- `default` required if ranges don't cover all possible values

**Validation rules (both modes):**
- `depends_on` column must exist (checked in `validate_dependencies`)
- `map` values must all be the same type
- `ranges` require numeric dependency column type (`int`, `float`)
- `default` required when coverage is not exhaustive

**Files:**
- `core/generators/conditional_generator.py` — `MapGenerator` and `RangeGenerator`
- `core/spec_validator.py` — add `_validate_conditional_column`
- `core/dataset_generator.py` — detect `map`/`ranges` keys and instantiate accordingly

---

## 8. Output Formats

**Format selection:** `?format=json` query param (default: `json`).

**Supported formats:**

| Format | `?format=` | Content-Type | Dependency |
|---|---|---|---|
| JSON array | `json` | `application/json` | stdlib |
| NDJSON | `ndjson` | `application/x-ndjson` | stdlib |
| CSV | `csv` | `text/csv` | stdlib `csv` |
| Parquet | `parquet` | `application/octet-stream` | `pyarrow` |
| Avro | `avro` | `application/avro` | `fastavro` |

**Files:**
- `core/formatters/` — new directory
  - `json_formatter.py`
  - `ndjson_formatter.py`
  - `csv_formatter.py`
  - `parquet_formatter.py`
  - `avro_formatter.py`
  - `__init__.py` — `get_formatter(format_str)` factory
- `api/routers/v1.py` — pass `?format` to formatter, return `StreamingResponse` with correct headers

**Response for non-JSON formats:**
```python
return StreamingResponse(
    formatter.stream(rows),
    media_type=formatter.content_type,
    headers={"Content-Disposition": f"attachment; filename=basalt.{fmt}"}
)
```

**Schema for Parquet/Avro:** inferred from the first row's types. `null` values use nullable schema.

**`/generate/multi` + formats:** each dataset returned as a separate file is not practical for multi-format. For non-JSON formats, `/generate/multi` only supports `json` and `ndjson`. Return 422 for other formats on multi.

---

## 9. `/validate` and `/infer` Endpoints

### `POST /v1/validate`
Runs validation without generating. Useful in CI pipelines and spec editors.

```
Request:  same payload as /v1/generate
Response 200: { "valid": true }
Response 422: { "valid": false, "error": "Column 'id': 'min' and 'max' must be integers" }
```

No rate limit adjustment needed — validation is cheap.

---

### `POST /v1/infer`
Given a sample JSON array of rows, infer a Basalt spec.

```
Request:  { "rows": [ {"id": 1, "name": "Alice", ...}, ... ], "seed": 42 }
Response: { "spec": { "rows": 10, "seed": 42, "columns": { ... } } }
```

**Inference rules per column:**

| Detected type | Inference |
|---|---|
| All int | `"type": "int"`, `min`/`max` from data |
| All float | `"type": "float"`, `min`/`max`, `rounding` from max decimal places |
| All bool | `"type": "boolean"`, `true_ratio` from data |
| String matching `YYYY-MM-DD` | `"type": "date"`, `start_date`/`end_date` from data |
| String matching ISO datetime | `"type": "timestamp"`, `start`/`end` from data |
| String matching UUID | `"type": "uuid"` |
| String matching email | `"type": "email"` |
| String matching `+\d` phone pattern | `"type": "phone"` |
| Low-cardinality string (≤ 20 unique values) | `"type": "string"` with `values` + `distribution` |
| High-cardinality string | `"type": "regex"` with inferred pattern (best-effort), falls back to `"type": "string"` with sampled values |
| Contains nulls | adds `null_ratio` |

**Files:**
- `core/inferrer.py` — new file, `infer_spec(rows, seed) -> dict`
- `api/routers/v1.py` — new endpoint

---

## 10. UI — Streamlit Spec Builder

**Approach:** Streamlit app in `ui/app.py`. Runs as a separate process alongside FastAPI. Calls the Basalt API over HTTP — no direct imports from `core/`. This keeps UI and API fully decoupled: the UI works against any deployed instance of Basalt, not just local.

**Run alongside API:**
```bash
# Terminal 1
uvicorn api.main:app --port 8000

# Terminal 2
streamlit run ui/app.py
# opens at http://localhost:8501
```

**Files:**
- `ui/app.py` — Streamlit app
- `ui/api_client.py` — thin wrapper around `requests` calls to the Basalt API
- `.env` / env var `BASALT_API_URL=http://localhost:8000` — points UI at any Basalt instance

**Streamlit app layout:**

```
┌─ Sidebar ──────────────────────────────┐
│  API URL (text input, default localhost)│
│  Seed (number input)                   │
│  Rows (slider 1–5000)                  │
│  Output format (selectbox)             │
└────────────────────────────────────────┘

┌─ Main area ────────────────────────────┐
│  [+ Add Column] button                 │
│                                        │
│  Per column (expander):                │
│    Column name (text input)            │
│    Type (selectbox)                    │
│    → Dynamic fields per type           │
│      int:  min, max, unique, sequential│
│      float: min, max, rounding         │
│      string: values+dist / depends_on  │
│      boolean: true_ratio               │
│      date: start_date, end_date        │
│      uuid: (none)                      │
│      timestamp: start, end             │
│      email: domains                    │
│      phone: format                     │
│      regex: pattern                    │
│    null_ratio (slider)                 │
│    [Remove] button                     │
│                                        │
│  ── Live Spec Preview ──               │
│  st.json(spec)   [Copy] [Download .json]│
│                                        │
│  [Validate]  [Generate]                │
│                                        │
│  ── Results ──                         │
│  st.dataframe(result)                  │
│  [Download CSV] [Download Parquet] ... │
└────────────────────────────────────────┘
```

**Key Streamlit features used:**
- `st.session_state` — holds column list across rerenders
- `st.expander` per column — keeps the UI compact with many columns
- `st.json` — live spec preview
- `st.dataframe` — renders result table with sorting/filtering built-in
- `st.download_button` — one button per output format, calls API with `?format=` param
- `st.tabs` — switch between "Builder" and "Paste Spec" (import existing JSON)

**Dependencies to add:**
```
streamlit==1.41.1
```

**No backend changes needed** — Streamlit calls the existing `/v1/generate`, `/v1/validate` endpoints over HTTP.

---

## New Files Summary

```
ui/
  app.py                         # Streamlit spec builder
  api_client.py                  # HTTP wrapper around Basalt API

api/
  routers/
    v1.py                        # all v1 endpoints
  rate_limit.py                  # slowapi setup
  main.py                        # updated: mounts router

core/
  generators/
    sequential_int_generator.py
    regex_generator.py
    conditional_generator.py     # MapGenerator + RangeGenerator
  formatters/
    __init__.py                  # get_formatter factory
    json_formatter.py
    ndjson_formatter.py
    csv_formatter.py
    parquet_formatter.py
    avro_formatter.py
  inferrer.py                    # /infer logic
  spec_validator.py              # updated: cell limit, sequential, regex, conditional
  dataset_generator.py           # updated: new generators registered
```

---

## Dependencies to Add

```
slowapi==0.1.9        # rate limiting
rstr==3.2.2           # regex generation
fastavro==1.9.7       # Avro output
pyarrow==18.1.0       # Parquet output
streamlit==1.41.1     # UI (ui/ only, not needed for API-only deployments)
```

`pyarrow` is large (~40MB). Consider making it optional with a graceful 501 error: `"Parquet support requires pyarrow. Install with pip install pyarrow."` if import fails.

`streamlit` is UI-only — not imported by the API. Can be excluded from Lambda/Docker-API-only deployments. Consider a separate `requirements-ui.txt`.

---

## What to Build First (Recommended Order)

1. API versioning + backwards compat redirects
2. Pin requirements.txt
3. Row/cell limits (env-var backed)
4. Rate limiter
5. `/validate` endpoint (trivial — 10 lines)
6. Sequential int + regex generators
7. Conditional generation
8. Output formats (CSV + NDJSON first — no new deps; then Parquet + Avro)
9. `/infer` endpoint
10. UI (last — depends on all endpoints being stable)
