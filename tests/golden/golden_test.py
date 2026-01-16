import json
import pytest
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset

@pytest.fixture
def spec_validator():
    return SpecValidator()

def test_golden_dataset():
    with open("tests/golden/input.json") as f:
        payload = json.load(f)

    with open("tests/golden/output.json") as f:
        expected = json.load(f)

    actual = generate_dataset(payload)

    assert actual == expected
