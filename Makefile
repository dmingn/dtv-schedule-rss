.PHONY: format-test
format-test: format test

.PHONY: test
test:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy .
	uv run python -m pytest -svx

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

DATE := $(shell date +%Y.%m.%d)
EXISTING_TAGS := $(shell gh release list --json tagName -q '.[] | .tagName' | grep '^$(DATE)')

.PHONY: create-release
create-release:
	@N=1; \
	while echo "$(EXISTING_TAGS)" | grep -q "^$(DATE).$$$${N}"; do \
		N=$$(($$N + 1)); \
	done; \
	TAG="$(DATE).$$N"; \
	echo "Creating GitHub release for tag: $$TAG"; \
	gh release create $$TAG --generate-notes
