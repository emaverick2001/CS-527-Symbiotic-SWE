FROM python:3.11-slim

ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock README.md /app/
COPY src /app/src
COPY configs /app/configs
COPY tests /app/tests
COPY docs /app/docs

RUN poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "symbiotic-swe", "--help"]
