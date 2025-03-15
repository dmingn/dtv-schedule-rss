.PHONY: test
test:
	pipenv run python -m pytest -svx

.PHONY: run-dev
run-dev:
	pipenv run uvicorn app.main:app --reload
