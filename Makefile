# Makefile

# Install core and dev dependencies
install:
	pip install -r requirements.txt -r requirements-dev.txt

# Run tests with coverage
test:
	pytest --cov=src --cov-report=term-missing

# Lint with ruff
lint:
	ruff check src tests

# Type check with mypy
type:
	mypy src

# Full CI run
ci: install lint type test

