FROM python:3.11-slim

WORKDIR /app

COPY apps/backend/pyproject.toml ./pyproject.toml
COPY apps/backend/src ./src

RUN pip install --upgrade pip && \
    pip install -e .[dev]

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "dealflow_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
