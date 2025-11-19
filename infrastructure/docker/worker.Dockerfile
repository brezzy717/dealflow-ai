FROM python:3.11-slim

WORKDIR /app

COPY apps/worker/pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY apps/worker/src ./src

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "dealflow_worker.main"]
