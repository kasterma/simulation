.PHONY: unittests
unittests:
	poetry run pytest tests/

.PHONY: format
format:
	ruff format

.PHONY: lint
lint:
	ruff check
	mypy src
