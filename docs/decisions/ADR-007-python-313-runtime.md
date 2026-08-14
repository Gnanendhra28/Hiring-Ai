# ADR-007: Standardizing on Python 3.13 Runtime Environment

## Status
Approved

## Context
Python 3.13 introduces performance improvements, enhanced async runtime support, improved error tracebacks, and typing advancements. To prevent technical debt and early runtime migration churn, the backend foundation is standardized on Python 3.13.

## Decision
1. Standardize backend project specifications to **Python 3.13** (`requires-python = ">=3.13"`).
2. Configure static tools for Python 3.13 target compliance:
   - Ruff: `target-version = "py313"`
   - Mypy: `python_version = "3.13"`
3. Docker images and container definitions build from `python:3.13-slim`.
4. Remove obsolete dependencies (e.g. `psycopg2-binary`, since `asyncpg` is the dedicated async driver for SQLAlchemy 2.x).

## Consequences
- Modern runtime foundation, enhanced execution performance, and elimination of legacy driver dependencies.
