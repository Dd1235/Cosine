const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const express = require("express");
const { createHealthRouter } = require("./health");

// The endpoint itself: cheap, cookie-free, uncached.
(async () => {
  const app = express();
  app.use(createHealthRouter({ problems: [{}, {}, {}], bootStart: Date.now() - 1500 }));
  const server = app.listen(0);
  const port = server.address().port;
  const res = await fetch(`http://127.0.0.1:${port}/healthz`);
  const body = await res.json();
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("set-cookie"), null, "a ping must not mint a visitor cookie");
  assert.equal(res.headers.get("cache-control"), "no-store");
  assert.equal(body.ok, true);
  assert.equal(body.problems, 3);
  assert.ok(body.uptimeMs >= 1500, "uptime is measured from the boot timestamp handed in");
  server.close();

  // The property that matters cannot be proven by a router test: that in the
  // real app the health route is mounted BEFORE the middleware that sets the
  // cookie and BEFORE the one that logs a visit. Guard the ordering in source.
  const src = fs.readFileSync(path.join(__dirname, "..", "index.js"), "utf8");
  const mount = src.indexOf("createHealthRouter(");
  const cookie = src.indexOf("cookieParser()");
  const visit = src.indexOf('logEvent("visit"');
  assert.ok(mount > -1 && cookie > -1 && visit > -1, "expected all three in server/index.js");
  assert.ok(mount < cookie, "/healthz must be mounted before cookieParser");
  assert.ok(mount < visit, "/healthz must be mounted before the visit logger");
  // Cold starts used to wait for ONNX model creation and warm-up before the
  // socket existed. The production default is lexical, so the listener must
  // be live before optional dense initialization begins.
  const listen = src.indexOf("app.listen(PORT");
  const afterListen = src.slice(listen);
  assert.ok(listen > -1, "expected the HTTP listener in server/index.js");
  assert.ok(afterListen.includes("setTimeout(async () =>"), "optional rankers should be deferred");
  assert.ok(
    afterListen.indexOf("registerDense(indexes, problems)") > afterListen.indexOf("setTimeout(async () =>"),
    "dense initialization must run after listen() on the bm25 default path"
  );
  console.log("health endpoint tests passed (cookie-free, uncached, mounted first)");
})().catch((err) => { console.error(err); process.exitCode = 1; });
