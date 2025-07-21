# ---- Base Stage ----
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.2


# ---- Builder Stage ----
FROM base as builder

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-dev


# ---- Final Stage ----
FROM base as final

COPY --from=builder /app /app

COPY ./src ./src
COPY ./alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]