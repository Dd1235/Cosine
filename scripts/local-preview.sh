#!/usr/bin/env bash
# Existing isolated preview only. Never source .env or run production migrations.
set -euo pipefail
cd "$(dirname "$0")/.."
export DATABASE_URL='postgresql://algolens@127.0.0.1:55433/algolens_preview'
export JWT_SECRET='local-preview-only-jwt-secret'
export HANDLE_KEY='local-preview-only-handle-secret'
export NODE_ENV=development TELEMETRY=off
export CANONICAL_HOST='' GOOGLE_CLIENT_ID='' GOOGLE_SHEETS_CLIENT_ID='' GRPC_BM25_ADDR=''
export PORT="${PORT:-3100}"
exec node server/index.js
