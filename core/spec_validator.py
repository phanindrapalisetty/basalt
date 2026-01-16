from typing import Dict, Any, List

ALLOWED_TYPES = {"int", "float", "string", "boolean", "date"}
MAX_ROWS = 1000


class SpecValidatorException(Exception):
    pass


class SpecValidator:
    @staticmethod
    def validate(spec: Dict[str, Any]) -> None:
        SpecValidator._validate_top_level(spec)
        SpecValidator._validate_columns(spec["columns"], spec["rows"])

    @staticmethod
    def _validate_top_level(spec: Dict[str, Any]) -> None:
        if not isinstance(spec, dict):
            raise SpecValidatorException("Spec must be a JSON object")

        # rows
        rows = spec.get("rows")
        if not rows:
            raise SpecValidatorException("'rows' is required")
        if not isinstance(rows, int) or rows <= 0 or rows > MAX_ROWS:
            raise SpecValidatorException(
                f"'rows' must be an integer between 1 and {MAX_ROWS}"
            )

        # columns
        columns = spec.get("columns")
        if not columns:
            raise SpecValidatorException("'columns' is required")
        if not isinstance(columns, dict) or not columns:
            raise SpecValidatorException("'columns' must be a non-empty JSON object")

        # seed
        seed = spec.get("seed")
        if not seed:
            raise SpecValidatorException("'seed' is required")
        if seed is not None and not isinstance(seed, int):
            raise SpecValidatorException("'seed' must be an integer, and is required")

    @staticmethod
    def _validate_columns(columns: Dict[str, Any], rows: int) -> None:
        for col_name in sorted(columns.keys()):
            col_spec = columns[col_name]

            # Column name
            if not isinstance(col_name, str):
                raise SpecValidatorException("Column names must be string")

            # name
            if not isinstance(col_spec, dict):
                raise SpecValidatorException(
                    f"Column '{col_spec}' must be a JSON object"
                )

            SpecValidator._validate_column(col_name, col_spec, rows)

    @staticmethod
    def _validate_column(name: str, spec: Dict[str, Any], rows: int) -> None:
        col_type = spec.get("type")

        if col_type not in ALLOWED_TYPES:
            raise SpecValidatorException(
                f"Column '{name}' has invalid type '{col_type}'"
            )

        null_ratio = spec.get("null_ratio", 0.0)
        unique = spec.get("unique", False)

        if not isinstance(null_ratio, float) or null_ratio < 0.0 or null_ratio > 1.0:
            raise SpecValidatorException(
                f"Column '{name}': 'null_ratio' must be a float between 0 and 1"
            )
        if not isinstance(unique, bool):
            raise SpecValidatorException(f"Column '{name}': 'unique' must be boolean")
        if unique is True and null_ratio > 0.0:
            raise SpecValidatorException(
                f"Column '{name}': 'unique' cannot be True if 'null_ratio' > 0.0"
            )

        if null_ratio != 0.0:
            SpecValidator._validate_null_ratio(name, null_ratio, rows)

        # column types validation
        if col_type == "string":
            SpecValidator._validate_string_column(name, spec, col_type, rows, unique)
        elif col_type == "int":
            SpecValidator._validate_int_column(name, spec, col_type, rows, unique)
        elif col_type == "float":
            SpecValidator._validate_float_column(name, spec, col_type, rows, unique)
        elif col_type == "boolean":
            SpecValidator._validate_boolean_column(name, spec, rows)
        elif col_type == "date":
            SpecValidator._validate_date_column(name, spec, col_type, rows, unique)

    @staticmethod
    def _validate_string_column(
        name: str, spec: Dict[str, Any], col_type: str, rows: int, unique: bool
    ) -> None:
        distribution = spec.get("distribution")
        values = spec.get("values")
        depends_on = spec.get("depends_on")
        null_ratio = spec.get("null_ratio", 0.0)

        if values is not None:
            SpecValidator._validate_values(
                name, values, col_type, distribution, unique, rows
            )
            SpecValidator._validate_distribution(name, distribution, null_ratio, rows)
            if depends_on is not None:
                raise SpecValidatorException(
                    f"Column '{name}': 'depends_on' cannot be specified if 'values' is specified"
                )
        elif depends_on is not None:
            if values is not None:
                raise SpecValidatorException(
                    f"Column '{name}': 'values' cannot be specified if 'depends_on' is specified"
                )

            if not isinstance(depends_on, str):
                raise SpecValidatorException(
                    f"Column '{name}': 'depends_on' must be a string"
                )
        else:
            raise SpecValidatorException(
                f"Column '{name}': 'values' or 'depends_on' must be specified for string type"
            )
        pass

    @staticmethod
    def _validate_int_column(
        name: str, spec: Dict[str, Any], col_type: str, rows: int, unique: bool
    ) -> None:
        min_val = spec.get("min")
        max_val = spec.get("max")

        if min_val > max_val:
            raise SpecValidatorException(
                f"Column '{name}': 'min' must be less than or equal to 'max'"
            )

        if not isinstance(min_val, int) or not isinstance(max_val, int):
            raise SpecValidatorException(
                f"Column '{name}': 'min' and 'max' must be integers"
            )

        if unique is True and (max_val - min_val + 1) < rows:
            raise SpecValidatorException(
                f"Column '{name}': 'unique' cannot be True if 'max' - 'min' + 1 < rows"
            )

    @staticmethod
    def _validate_float_column(
        name: str, spec: Dict[str, Any], col_type: str, rows: int, unique: bool
    ) -> None:
        min_val = spec.get("min")
        max_val = spec.get("max")

        if min_val > max_val:
            raise SpecValidatorException(
                f"Column '{name}': 'min' must be less than or equal to 'max'"
            )

        if not isinstance(min_val, float) or not isinstance(max_val, float):
            raise SpecValidatorException(
                f"Column '{name}': 'min' and 'max' must be floats"
            )

        if unique is True:
            raise SpecValidatorException(
                f"Column '{name}': 'unique' cannot be relaised for a float type"
            )

    @staticmethod
    def _validate_boolean_column(name: str, spec: Dict[str, Any], rows: int) -> None:
        true_ratio = spec.get("true_ratio")
        null_ratio = spec.get("null_ratio", 0.0)

        if not isinstance(true_ratio, float):
            raise SpecValidatorException(
                f"Column '{name}': 'true_ratio' must be a float"
            )

        if true_ratio < 0 or true_ratio > 1:
            raise SpecValidatorException(
                f"Column '{name}': 'true_ratio' must be between 0 and 1"
            )

        if not (rows * true_ratio).is_integer():
            raise SpecValidatorException(
                f"Column '{name}': 'true_ratio' cannot be realized"
            )

        if true_ratio + null_ratio > 1:
            raise SpecValidatorException(
                f"Column '{name}': 'true_ratio' + 'null_ratio' must be <= 1"
            )

    @staticmethod
    def _validate_date_column(
        name: str, spec: Dict[str, Any], col_type: str, rows: int, unique: bool
    ) -> None:
        start_date = spec.get("start_date")
        end_date = spec.get("end_date")

        if not isinstance(start_date, str) or not isinstance(end_date, str):
            raise SpecValidatorException(
                f"Column '{name}': date columns require 'start' and 'end' (ISO strings)"
            )

    @staticmethod
    def _validate_distribution(
        name: str, distribution, null_ratio: float, rows: int
    ) -> None:
        if isinstance(distribution, list):
            for p in distribution:
                expected = rows * p
                if not isinstance(p, float):
                    raise SpecValidatorException(
                        f"Column '{name}': 'distribution' must be a list of floats"
                    )
                if not expected.is_integer():
                    raise SpecValidatorException(
                        f"Column '{name}': 'distribution' {p} cannot be realized"
                    )
            if sum(distribution) + null_ratio < 1e-6:
                raise SpecValidatorException(
                    f"Column '{name}': 'distribution' and/or 'null_ratio' must sum to 1.0"
                )

            # Sanity Check
            total = sum([int(rows * p) for p in distribution]) + int(rows * null_ratio)
            if total != rows:
                raise SpecValidatorException(
                    f"Column '{name}': 'distribution' does not sum to 'rows'"
                )
        elif (
            isinstance(distribution, str) and distribution == "uniform"
        ) or distribution is None:
            # pass
            raise SpecValidatorException(
                f"Column '{name}': 'distribution' must be a list of floats and not a string"
            )

        else:
            raise SpecValidatorException(
                f"Column '{name}': 'distribution' must be a list of floats or 'uniform'"
            )

    @staticmethod
    def _validate_values(
        name: str,
        values: List[Any],
        type: str,
        distribution,
        unique: bool,
        rows: int,
    ) -> None:
        if not values or len(values) == 0:
            raise SpecValidatorException(f"Column '{name}': 'values' must be non-empty")

        if not isinstance(values, list):
            raise SpecValidatorException(f"Column '{name}': 'values' must be a list")
        if not distribution:
            raise SpecValidatorException(
                f"Column '{name}': 'values' must have a 'distribution'"
            )
        if unique is True:
            raise SpecValidatorException(
                f"Column '{name}': 'unique' is not supported for 'values'"
            )
        for v in values:
            if type == "int" and not isinstance(v, int):
                raise SpecValidatorException(
                    f"Column '{name}': 'values' must be a list of int"
                )
            if type == "float" and not isinstance(v, float):
                raise SpecValidatorException(
                    f"Column '{name}': 'values' must be a list of float"
                )
            if type == "string" and not isinstance(v, str):
                raise SpecValidatorException(
                    f"Column '{name}': 'values' must be a ENUM string"
                )
        if len(values) != len(distribution):
            raise SpecValidatorException(
                f"Column '{name}': 'values' and 'distribution' must have the same length"
            )

    @staticmethod
    def _validate_null_ratio(name: str, null_ratio: float, rows: int) -> None:
        if not isinstance(null_ratio, float):
            raise SpecValidatorException(
                f"Column '{name}': 'null_ratio' must be a float"
            )
        if null_ratio < 0.0 or null_ratio > 1.0:
            raise SpecValidatorException(
                f"Column '{name}': 'null_ratio' must be between 0.0 and 1.0"
            )

        if not (rows * null_ratio).is_integer():
            raise SpecValidatorException(
                f"Column '{name}': 'null_ratio: {null_ratio}' for {rows} rows cannot be realized"
            )
