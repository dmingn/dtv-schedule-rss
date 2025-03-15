FROM python:3.13

RUN groupadd -g 1000 appgroup && \
    useradd -m -u 1000 -g appgroup appuser

WORKDIR /workdir

RUN pip install pipenv==2024.4.1

COPY Pipfile Pipfile.lock ./

RUN pipenv install --deploy --system

COPY app ./app

USER appuser:appgroup

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
