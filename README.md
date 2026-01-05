# Basalt
A service that guarantees deterministic output: the same input specification and seed will always produce identical results. A deterministic, constraint-driven synthetic data API for data engineers.

# Folder Structure
basalt/
├── api/
│   └── handler.py
├── core/
│   ├── spec.py
│   ├── constraints.py
│   ├── generators.py
│   └── random.py
├── tests/
│   └── test_determinism.py
├── README.md
└── requirements.txt
