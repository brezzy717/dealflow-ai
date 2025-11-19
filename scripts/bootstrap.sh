#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install -e apps/backend[dev]
pip install -e apps/worker[dev]
pushd apps/frontend >/dev/null
npm install
popd >/dev/null
echo "Bootstrap complete."
