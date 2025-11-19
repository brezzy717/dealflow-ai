FROM python:3.11-slim

WORKDIR /app

COPY apps/worker/pyproject.toml ./pyproject.toml
COPY apps/worker/src ./src

RUN pip install --upgrade pip && \
    pip install -e .

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "dealflow_worker.main"]
