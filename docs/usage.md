# Usage Overview
## Top Level Fields
`rows`
- number of rows to generate, maxed out at 1000 as of now
```json
"rows": 5
```

`seed` 
- a random number input, should be an integer and is mandatory
```json
"seed": 49
```

`columns` 
- defines the dataset schema and should be a JSON 
- keys represent the column names
- values represent the column types
- column order doesn't affect the output
```json
"columns": {
    "id": { ... },
    "is_active": { ... }
}
```

## Column Types
`int`
- `min_val` and `max_val` are mandatory and are of type integers
- `unique` is optional, should be a boolean if given
- `null_ratio` is optional, should be a float between 0 and 1
```json
"columns": {
    "id": {
        "type": "int",
        "min_val": 1,
        "max_val": 100,
        "unique": true,
        "null_ratio": 0.1
    }
}
```

`float`
- `min_val` and `max_val` are mandatory and are of type floats
- `null_ratio` is optional, should be a float between 0 and 1
- `rounding` is optional, should be an integer if given, default to 6 if not provided
```json
"columns": {
    "price": {
        "type": "float",
        "min_val": 1.5,
        "max_val": 100.5,
        "null_ratio": 0.1,
        "rounding": 2
    }
}
```

`boolean`
- `true_ratio` is mandatory, should be a float between 0 and 1
- `null_ratio` is optional, should be a float between 0 and 1
```json
"columns": {
    "is_active": {
        "type": "boolean",
        "true_ratio": 0.7,
        "null_ratio": 0.1
    }
}
```

`string`: dependent type
- `depends_on` is mandatory, should be a string. This is the column name that the current column depends on.
- `template`
```json
"columns": {
    "id": {
        "type": "int",
        "min_val": 1,
        "max_val": 100,
        "unique": true,
        "null_ratio": 0.1
    }, 
    "email": {
        "type": "string",
        "depends_on": "id",
        "template": "id_{value}@gmail.com"
    }
}
```

`string`: distribution type

- `values` categorical values which are to be. Must contain at least one value. Values are used exactly as provided. This is a mandatory field.
- `distribution` controls how string values are distributed across rows. Should be a list of floats between 0 to 1. The sum of distribution is to be summed to 1 including `null_ratio`. This is a mandatory field.
- `null_ratio` is optional, should be a float between 0 and 1.

```json
"columns": {
    "gender": {
        "type": "string",
        "values": ["male", "female"],
        "distribution": [0.4, 0.4],
        "null_ratio": 0.2
    }
}
```

`date`
- `min_date` and `max_date` are mandatory and are of type string. The format is `YYYY-MM-DD`.
- `null_ratio` is optional, should be a float between 0 and 1.
```json
"columns": {
    "date_of_birth": {
        "type": "date",
        "min_date": "1990-01-01",
        "max_date": "2000-12-31",
        "null_ratio": 0.1
    }
}
```

### Note
- `null_ratio` is only realised only when `unique` is not set to true.
- Any of the ratios `null_ratio`, `true_ratio`, `distribution` can be only realised only when the rows can be realised. That means, the multiplication of any `ratio` and `rows` should be an integer. Rounding of cannot be achieved as it affects determinism. If the ratio cannot be realised, an error will be thrown.
- Currently `string` whcih has `depends_on` is supported for only one independent column. It can be further extended to support multiple columns.