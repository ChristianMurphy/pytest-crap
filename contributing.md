# Contributing to pytest-crap

Thank you for your interest in contributing! This guide will help you get set up for development.

## Development Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/pytest-crap.git
   cd pytest-crap
   ```

2. Install dependencies with Poetry:

   ```bash
   poetry install
   ```

3. Activate the virtual environment:

   ```bash
   poetry shell
   ```

## Running Tests

Run the test suite with coverage:

```bash
poetry run pytest
```

This will automatically run with coverage enabled (configured in `pyproject.toml`).

To run without coverage:

```bash
poetry run pytest --no-cov
```

## Code Quality

### Linting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

Check for linting issues:

```bash
poetry run ruff check .
```

Auto-fix linting issues:

```bash
poetry run ruff check --fix .
```

### Formatting

Check formatting:

```bash
poetry run ruff format --check .
```

Apply formatting:

```bash
poetry run ruff format .
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) with strict mode enabled.

```bash
poetry run mypy pytest_crap
```

## Running All Checks

Before submitting a PR, ensure all checks pass:

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy pytest_crap
poetry run pytest
```

## Project Structure

```
pytest-crap/
├── pytest_crap/
│   ├── __init__.py      # Package version
│   ├── calculator.py    # CRAP score computation
│   ├── mapper.py        # AST-based function extraction
│   ├── plugin.py        # pytest plugin hooks
│   ├── reporter.py      # Rich-based terminal output
│   └── py.typed         # PEP 561 marker
├── stubs/
│   └── radon/           # Type stubs for radon library
├── tests/
│   ├── conftest.py      # pytest fixtures
│   ├── test_calculator.py
│   ├── test_mapper.py
│   ├── test_plugin.py   # Integration tests using pytester
│   └── test_reporter.py
└── pyproject.toml       # Project configuration
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-json-output`
- `fix/handle-syntax-errors`
- `docs/improve-readme`

### Creating a Branch

1. Create a new branch for your feature or fix:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests

3. Ensure all checks pass (see above)

4. Commit with a clear message:

   ```bash
   git commit -m "Add feature X that does Y"
   ```

   For larger changes, use a detailed commit message:

   ```
   Add JSON output format for CI integration

   - Add --crap-format option (terminal, json)
   - Create JsonReporter class
   - Add tests for JSON output
   ```

5. Push and open a Pull Request

### Pull Request Guidelines

When opening a PR, include:

- **What**: Brief description of the change
- **Why**: Motivation for the change
- **How**: Implementation approach (if non-obvious)
- **Testing**: How the change was tested

## Code Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) (enforced by Ruff)
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and reasonably sized
- Add tests for new functionality

## Testing Guidelines

- Use `pytester` fixture for integration tests that need to run pytest
- Use `tempfile` for unit tests that need temporary Python files
- Mock external dependencies when appropriate
- Aim for high coverage, but prioritize meaningful tests over coverage percentage

## Releasing

Releases are managed by maintainers. The process:

1. Update version in `pytest_crap/__init__.py`
2. Update CHANGELOG
3. Create a git tag
4. Build and publish to PyPI

## Questions?

Open an issue for any questions about contributing.

## Reporting Issues

When reporting bugs, please include:

- Python version (`python --version`)
- pytest-crap version
- Minimal reproduction steps
- Expected vs actual behavior
- Full error traceback if applicable

## Feature Requests

Feature requests are welcome! Please describe:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered
