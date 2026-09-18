const { Pool } = require("pg");

// Single Pool for the lifetime of the process. node-postgres queues queries
// and reuses connections; we don't manually acquire/release.
let pool = null;

function getPool() {
  if (pool) return pool;
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    throw new Error(
      "DATABASE_URL is not set. Copy .env.example to .env and set DATABASE_URL, or run `docker compose up -d` and export it."
    );
  }
  pool = new Pool({
    connectionString,
    // Bound pool acquisition/connection and SQL execution separately. A
    // sleeping hosted database must not leave auth/library requests queued
    // indefinitely (telemetry shares this pool too).
    connectionTimeoutMillis: 5000,
    statement_timeout: 8000,
    // Managed Postgres (Render, Neon, etc.) requires SSL; local docker-compose
    // doesn't. node-postgres ignores `sslmode` in the URL, so flip ssl on
    // explicitly whenever the URL asks for it — keeps local dev cert-free.
    ssl: /sslmode=require/.test(connectionString) ? { rejectUnauthorized: false } : false,
  });
  // An idle connection can disappear when a hosted database suspends. The
  // pool replaces it on demand; an unhandled error would crash the web app.
  pool.on("error", (error) => console.warn("Idle database connection lost:", error.code || "connection_error"));
  return pool;
}

async function query(text, params) {
  return getPool().query(text, params);
}

async function close() {
  if (pool) {
    await pool.end();
    pool = null;
  }
}

module.exports = { getPool, query, close };
