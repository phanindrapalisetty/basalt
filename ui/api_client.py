import os
import requests

BASALT_API_URL = os.getenv("BASALT_API_URL", "http://localhost:8000")


def generate(spec: dict, fmt: str = "json") -> requests.Response:
    return requests.post(f"{BASALT_API_URL}/generate?format={fmt}", json=spec, timeout=30)


def validate(spec: dict) -> requests.Response:
    return requests.post(f"{BASALT_API_URL}/validate", json=spec, timeout=10)


def infer(rows: list, seed: int = 42) -> requests.Response:
    return requests.post(f"{BASALT_API_URL}/infer", json={"rows": rows, "seed": seed}, timeout=10)


def health() -> bool:
    try:
        r = requests.get(f"{BASALT_API_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False
