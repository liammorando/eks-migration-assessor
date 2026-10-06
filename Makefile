# Makefile for EKS Migration Assessor

.PHONY: check test lint perf selfcheck clean

# Run all tests
test:
	python -m pytest -q

# Run linting (ruff)
lint:
	python -m ruff check src app tests scripts

# Run performance tests
perf:
	python -m pytest tests/test_perf.py -v -m perf -s

# Run full self-check
selfcheck:
	python scripts/selfcheck.py

# Quick check (test + lint)
check: test lint

# Clean up temporary files
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	rm -rf tests/__pycache__ app/__pycache__ src/__pycache__
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run with coverage
coverage:
	python -m pytest --cov=assessor --cov=app --cov-report=term-missing

# Format code with ruff
format:
	python -m ruff format src app tests scripts

# Fix auto-fixable ruff issues
fix:
	python -m ruff check --fix src app tests scripts