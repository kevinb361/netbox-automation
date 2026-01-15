.PHONY: format lint type test ci install clean

format:
	black src/ tests/
	ruff check --fix src/ tests/

lint:
	ruff check src/ tests/

type:
	mypy src/

test:
	pytest || [ $$? -eq 5 ]

ci: format lint type test

install:
	pip install -e ".[dev]"

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
