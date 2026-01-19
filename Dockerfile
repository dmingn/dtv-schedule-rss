FROM python:3.13

RUN groupadd -g 1000 appgroup && \
    useradd -m -u 1000 -g appgroup appuser

WORKDIR /workdir

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY templates ./templates
COPY app ./app

USER appuser:appgroup

ENTRYPOINT [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
