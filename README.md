# pytest-crap

A pytest plugin that calculates CRAP scores (Cyclomatic Complexity × Coverage Risk) and displays prioritized lists of high-risk functions to guide test writing.

## Installation

```bash
pip install pytest-crap
```

## Usage

```bash
pytest --crap --crap-threshold=30 --crap-top-n=20
```

## Development

Install with poetry:

```bash
poetry install
```

Run tests:

```bash
poetry run pytest
```

Run linting:

```bash
poetry run ruff check .
poetry run ruff format .
```

Run type checks:

```bash
poetry run mypy pytest_crap
```
