.PHONY: test
test:
	pipenv run python -m pytest -svx

.PHONY: run-dev
run-dev:
	pipenv run uvicorn app.main:app --reload

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
