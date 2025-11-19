#!/usr/bin/env bash
set -euo pipefail

echo "Formatting backend..."
(cd apps/backend && ruff format src)
echo "Formatting worker..."
(cd apps/worker && ruff format src)
echo "Formatting frontend..."
(cd apps/frontend && npm run lint -- --fix)
