# Basalt
A synthetic data generator that guarantees deterministic output: the same input specification and seed will always produce identical results. It's for engineers who care about **reproducibility, schema stability, and test reliability**.


This project treats synthetic data as **compiled output**, not random samples. If your tests, pipelines, or analytics depend on **stable data**, this tool is built for you.

> same input schema + same constraints +same seed = **identical output. Always.**[^](#important-note)

It's lightweight, simple and boringly written. 

## Folder Structure
```
basalt/
├── api/
│   ├── main.py
│   └── lambda_handler.py
├── core/
│   ├── spec_validator.py
│   ├── random_context.py
│   ├── dataset_generator.py
│   └── generators
│       ├── int_generator.py
│       ├── boolean_generator.py
│       ├── float_generator.py
│       └── derived_generator.py
├── tests/
│   └── golden/
├── docs/
├── Dockerfile
├── README.md
├── LICENSE
└── requirements.txt
```

## Core Philosophy

This tool enforces **hard determinism contracts**:

- Same payload + same seed → same dataset
- Adding a new column does **not** change existing columns
- Column order does **not** affect values
- No hidden global randomness
- Determinism is tested, not assumed

If any of these break, it’s considered a **bug**, not acceptable behavior.


## Features

- Deterministic row generation
- Supported column types:
  - `int` (min, max, unique, null_ratio)
  - `boolean` (true_ratio, null_ratio)
  - `float` (min, max, rounding, null_ratio)
  - `string` (depends_on, distribution)
  - `date` (min, max, null_ratio)
- Schema-driven generation
- Fully seed-controlled output
- Per-column random generators

Check out the [documentation](/docs/features.md) on features.

### Important note
> Deterministic output is guaranteed for a given input specification and seed within the same engine version.
Changes to the core generation logic (the engine) may result in different outputs, even when the input spec and seed remain unchanged.

## Example

### Input schema
```json
{
  "rows": 5,
  "seed": 49,
  "columns": {
    "id": {
      "type": "int",
      "min": 1,
      "max": 100,
      "unique": true
    },
    "is_active": {
      "type": "boolean",
      "true_ratio": 0.4
    }
  }
}
```
### Output (guaranteed stable)
```json 
[
  {"id": 64, "is_active": true},
  {"id": 9, "is_active": false},
  {"id": 20, "is_active": false},
  {"id": 7, "is_active": false},
  {"id": 90, "is_active": true}
]
```

Check out the [documentation](/docs/usage.md) for more details on usage.


## API Usage

Check out the [documentation](/docs/api-usage.md) for details on API. 

Here is the  swagger UI for the hosted service: https://basalt.bundl-spaces.com/docs.
Would like to self-host? Head over [here](docs/hosting.md) to explore more. 
This [medium article](https://medium.com/@phanindra-palisetty/deploying-a-public-fastapi-on-aws-lambda-using-ecr-and-api-gateway-aaceeaccd04e) can help in deploying to AWS Lambda via API Gateway with predictable costs and minimal operational overhead. 

## Design Principles

- No shared global RNG
- Each column owns its randomness
- Explicit generation order
- Zero implicit shuffling
- Fail fast on invalid specs

**High Level Design**
```markdown
HTTP POST /generate
        |
        v
+----------------------+
| Spec Validator       |
+----------------------+
        |
        v
+----------------------+
| RandomContext (seed) |
+----------------------+
        |
        v
+----------------------+
| Dataset Generator    |
+----------------------+
        |
        v
+----------------------+
| JSON Serializer      |
+----------------------+
        |
        v
HTTP 200 (JSON array)
```

## Use Cases

- Backend API testing
- Analytics pipeline testing
- Reproducible demos and dashboards
- Contract testing
- Snapshot testing

Anywhere **data stability matters more than realism**.

## What This Is (and Isn’t)

### This is:
- A test data compiler
- CI-friendly
- Engineer-first

### This is not:
- A Faker alternative
- A realism engine
- A ML synthetic data tool


## Status

- Actively built  
- Focused on correctness over features  
- Heavy test coverage
- A rate limiter is expected in future which limits `10 requests per minute per IP`, yes I'm poor..


## Call to Action

If you believe **determinism is a feature, not an option**, this tool is for you.

👉 Check out the GitHub repository  
👉 Read the determinism guarantees  
👉 Try breaking it (seriously)

**Shoutout to**
- [black](https://pypi.org/project/black/) module for formatting the code.
- [hotheadhacker](https://github.com/hotheadhacker/no-as-a-service) for inspiration.
