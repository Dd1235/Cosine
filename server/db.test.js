const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const { EventEmitter } = require("node:events");
const warnings = [];
const instances = [];
class FakePool extends EventEmitter {
  constructor(options) { super(); this.options = options; instances.push(this); }
  async query(text) { return {text}; }
  async end() { this.closed = true; }
}
const ctx = vm.createContext({
  require: name => { assert.equal(name, "pg"); return {Pool: FakePool}; },
  process: {env: {DATABASE_URL: "postgres://test@localhost/test"}},
  module: {exports: {}}, console: {warn: (...args) => warnings.push(args)},
});
vm.runInContext(fs.readFileSync(`${__dirname}/db.js`, "utf8"), ctx);
const db = ctx.module.exports;
(async () => {
  const pool = db.getPool();
  assert.equal(db.getPool(), pool);
  assert.equal(pool.options.connectionTimeoutMillis, 5000);
  assert.equal(pool.options.statement_timeout, 8000);
  pool.emit("error", Object.assign(new Error("contains a private hostname"), {code: "ECONNRESET"}));
  assert.equal(warnings.length, 1, "idle failure handled rather than crashing");
  assert.ok(!JSON.stringify(warnings).includes("hostname"), "do not log connection details");
  assert.equal((await db.query("SELECT 1")).text, "SELECT 1");
  await db.close();
  assert.ok(pool.closed);
  assert.notEqual(db.getPool(), pool);
  assert.equal(instances.length, 2);
  await db.close();
  console.log("database pool lifecycle and timeout tests passed");
})().catch(error => {console.error(error); process.exitCode = 1;});
