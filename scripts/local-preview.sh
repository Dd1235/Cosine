#!/usr/bin/env bash
# Local app using the database and secrets configured in .env.
# No migrations. Changes made in the UI affect that database (including prod).
set -euo pipefail
cd "$(dirname "$0")/.."
export NODE_ENV=development TELEMETRY=off
export CANONICAL_HOST='' GRPC_BM25_ADDR=''
export PORT="${PORT:-3100}"
# Validate connectivity without changing data. dotenv is parsed by Node, never
# sourced as shell commands, and credentials are never printed.
node - <<'NODE'
require('dotenv').config({ quiet: true });
const db = require('./server/db');
(async () => {
  try {
    require('./server/crypto/secrets').assertKeyPresent();
    await db.query('SELECT id FROM users LIMIT 0');
    console.log('Configured database reachable. Localhost uses real account data; no migrations were run.');
  } catch (_) {
    console.error('Preview cannot reach the configured database or required secrets are missing. Check .env and network connectivity.');
    process.exitCode = 1;
  } finally { await db.close(); }
})();
NODE
exec node server/index.js
