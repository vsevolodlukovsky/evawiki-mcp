# Contributing to evawiki-mcp

## Development setup

1. Clone the repository:
   ```bash
   git clone https://github.com/vsevolodlukovsky/evawiki-mcp.git
   cd evawiki-mcp
   ```

2. Create a virtual environment and install the package in editable mode with dev dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Before submitting a PR

- Run linting and formatting:
  ```bash
  ruff check .
  ruff format --check .
  ```
  Or with pre-commit (runs on staged files):
  ```bash
  pre-commit run --all-files
  ```

- Run tests:
  ```bash
  pytest
  ```

## Requirements

- Python 3.10+
- Dev tools: pytest, ruff (installed via `pip install -e ".[dev]"`).

## Releasing

- Version is kept in `pyproject.toml` (SemVer).
- Release: create a git tag `v0.1.0` (match version in pyproject.toml), push, then create a GitHub Release.
- Optionally: build wheel/sdist and publish to PyPI (e.g. via GitHub Action or manual `twine upload`).
