FROM python:3.11-slim

WORKDIR /app

COPY apps/backend/pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .[dev]

COPY apps/backend/src ./src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "dealflow_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
