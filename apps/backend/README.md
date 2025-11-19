# DealFlow Backend

FastAPI service responsible for authentication, broker operations, scoring orchestration, and integrations with the data layer.

## Key Commands
- `uvicorn dealflow_backend.main:app --reload` — start the API locally.
- `pytest` — execute unit tests.
- `ruff check .` — lint the code base.
- `mypy src` — run static type checks.

Configuration defaults live in `configs/settings/application.yaml`. Environment variables are sourced from `configs/env/backend.env.example`.
