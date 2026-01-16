import json
import pytest
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset

@pytest.fixture
def spec_validator():
    return SpecValidator()

def test_same_seed_same_output():
    """
    Determinism test (same input → same output)
    """
    payload = {"rows":70,"seed":-4,"columns":{"id":{"type":"int","min":1,"max":100,"unique":True},"is_active":{"type":"boolean","true_ratio":0.4}}}

    out1 = generate_dataset(payload)
    out2 = generate_dataset(payload)

    assert out1 == out2

def test_different_seed_changes_output():
    """
    Seed change test (different seed → different output). Ensures seed actually matters.
    """
    payload = {"rows":70,"seed":-4,"columns":{"id":{"type":"int","min":1,"max":100,"unique":True},"is_active":{"type":"boolean","true_ratio":0.4}}}

    out1 = generate_dataset({**payload, "seed": 1})
    out2 = generate_dataset({**payload, "seed": 2})

    assert out1 != out2
    
def test_column_order_does_not_matter():
    """
    Column order invariance
    """
    payload1 = {"rows":5,"seed":49,"columns":{"id":{"type":"int","min":1,"max":100,"unique":True},"is_active":{"type":"boolean","true_ratio":0.4}}}
    payload2 = {"rows":5,"seed":49,"columns":{"is_active":{"type":"boolean","true_ratio":0.4},"id":{"type":"int","min":1,"max":100,"unique":True}}}

    assert generate_dataset(payload1) == generate_dataset(payload2)

def test_adding_column_does_not_change_existing_data():
    """
    Schema evolution safety: Adding a column should not change existing data
    """
    base = {"rows":5,"seed":49,"columns":{"id":{"type":"int","min":1,"max":100,"unique":True},"is_active":{"type":"boolean","true_ratio":0.4}}}
    extended = {"rows":5,"seed":49,"columns":{"id":{"type":"int","min":1,"max":100,"unique":True},"is_active":{"type":"boolean","true_ratio":0.4}, "created_date": {"type": "date", "start_date": "2023-01-01", "end_date": "2023-12-31"}}}

    base_out = generate_dataset(base)
    extended_out = generate_dataset(extended)

    for i in range(len(base_out)):
        assert base_out[i]["id"] == extended_out[i]["id"]
        assert base_out[i]["is_active"] == extended_out[i]["is_active"]

def test_column_isolation():
    """
    Column isolation test: Changing one column's config should not affect others
    Proves per-column RNG correctness
    """
    base = {"rows":5,"seed":49,"columns":{"id":{"type":"int","min":1,"max":100,"unique":True},"is_active":{"type":"boolean","true_ratio":0.4}}}
    modified = {"rows":5,"seed":49,"columns":{"id":{"type":"int","min":1,"max":100,"unique":True},"is_active":{"type":"boolean","true_ratio":0.8}}}

    base_out = generate_dataset(base)
    mod_out = generate_dataset(modified)

    for i in range(len(base_out)):
        assert base_out[i]["id"] == mod_out[i]["id"]