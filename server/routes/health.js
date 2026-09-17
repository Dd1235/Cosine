const express = require("express");

// A liveness endpoint for the keep-alive pinger and Render's health check.
//
// It exists because `GET /` writes a `visit` event and sets a visitor cookie
// (server/index.js), so pointing a ten-minute cron at the home page would have
// inflated the visitor count by ~144 a day and stored a cookie nobody owns.
// This router is mounted before cookieParser, attachUser and the visitor
// middleware — see the ordering assertion in health.test.js — so a ping touches
// no database and leaves no trace beyond the process being awake.
function createHealthRouter({ problems = [], bootStart = Date.now() } = {}) {
  const router = express.Router();
  router.get("/healthz", (_req, res) => {
    res.set("Cache-Control", "no-store");
    res.json({ ok: true, uptimeMs: Date.now() - bootStart, problems: problems.length });
  });
  return router;
}

module.exports = { createHealthRouter };
