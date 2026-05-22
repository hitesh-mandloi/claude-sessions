.PHONY: help install dev-install test lint format build clean

help:
	@echo "make install      - pip install ."
	@echo "make dev-install  - pip install -e '.[dev]'"
	@echo "make test         - run pytest"
	@echo "make lint         - ruff check ."
	@echo "make format       - ruff format ."
	@echo "make build        - python -m build (sdist + wheel)"
	@echo "make clean        - remove build artifacts"

install:
	pip install .

dev-install:
	pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

build:
	python -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
