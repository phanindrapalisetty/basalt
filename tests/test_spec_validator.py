import pytest
from core.spec_validator import SpecValidator, SpecValidatorException


@pytest.fixture
def spec_validator():
    return SpecValidator()


def test_validate_spec_valid():
    spec = {
        "rows": 10,
        "seed": 42,
        "columns": {
            "client_id": {
                "type": "int",
                "min": 1,
                "max": 100,
            },
            "client_country": {
                "type": "string",
                "values": ["US", "UK", "CA"],
                "distribution": [0.3, 0.5, 0.2],
            },
        },
    }

    SpecValidator.validate(spec)


def test_spec_not_json_fails():
    spec = """{
        "rows": 3,
        "columns": {
            "client_id": {
                "type": "int",
                "min": 1,
                "max": 100,
            }
        }
    }"""

    with pytest.raises(SpecValidatorException, match="Spec must be a JSON object"):
        SpecValidator.validate(spec)


def test_missing_seed_fails():
    spec = {
        "rows": 3,
        "columns": {
            "client_id": {
                "type": "int",
                "min": 1,
                "max": 100,
            }
        },
    }

    with pytest.raises(SpecValidatorException, match="'seed' is required"):
        SpecValidator.validate(spec)


def test_missing_rows_fails():
    spec = {
        "seed": 42,
        "columns": {
            "client_id": {
                "type": "int",
                "min": 1,
                "max": 100,
            }
        },
    }

    with pytest.raises(SpecValidatorException, match="'rows' is required"):
        SpecValidator.validate(spec)


def test_missing_columns_fails():
    spec = {
        "rows": 3,
        "seed": 42,
    }

    with pytest.raises(SpecValidatorException, match="'columns' is required"):
        SpecValidator.validate(spec)


def test_missing_column_type_fails():
    spec = {
        "rows": 3,
        "seed": 42,
        "columns": {
            "client_id": {
                "min": 1,
                "max": 100,
            }
        },
    }

    with pytest.raises(SpecValidatorException):
        SpecValidator.validate(spec)


def test_missing_column_not_json_fails():
    spec = {
        "rows": 3,
        "seed": 42,
        "columns": """{"client_id": { "min": 1, "max": 100}}""",
    }

    with pytest.raises(SpecValidatorException):
        SpecValidator.validate(spec)

def test_invalid_distribution_not_sum_to_one():
    spec = {
        "rows": 3,
        "seed": 42,
        "columns": {
            "client_id": {
                "type": "int",
                "min": 1,
                "max": 100,
            },
            "client_country": {
                "type": "string",
                "values": ["US", "UK", "CA"],
                "distribution": [0.1, 0.2, 0.3],
            },
        },
    }

    with pytest.raises(SpecValidatorException, match = "Column 'client_country': 'distribution' 0.1 cannot be realized"):
        SpecValidator.validate(spec)