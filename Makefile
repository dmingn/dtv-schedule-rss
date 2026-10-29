.PHONY: format-test
format-test: format test

.PHONY: test
test:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy .
	uv run python -m pytest -sv tests/unit
	uv run python -m pytest -sv tests/integration

.PHONY: test-scrape
test-scrape:
	uv run python -m pytest -sv tests/scrape

.PHONY: test-all
test-all: test test-scrape

.PHONY: format
format:
	uv run ruff format .
	uv run ruff check --fix .

.PHONY: run-dev
run-dev:
	uv run uvicorn app.main:app --reload

.PHONY: up
up:
	docker-compose up --build
