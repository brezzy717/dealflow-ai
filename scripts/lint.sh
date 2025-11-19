#!/usr/bin/env bash
set -euo pipefail

echo "Linting backend..."
(cd apps/backend && ruff check src && mypy src)
echo "Linting worker..."
(cd apps/worker && ruff check src)
echo "Linting frontend..."
(cd apps/frontend && npm run lint)
