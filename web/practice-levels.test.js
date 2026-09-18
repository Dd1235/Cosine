const assert = require("node:assert/strict");
const fs = require("node:fs");
const {JSDOM} = require("jsdom");
const settle = async () => { for (let i = 0; i < 5; i++) await new Promise(setImmediate); };
(async () => {
  const dom = new JSDOM(fs.readFileSync(`${__dirname}/profile.html`, "utf8"), {url: "http://local/profile.html", runScripts: "outside-only"});
  const w = dom.window;
  let preferences = {levels: {codeforces: {min: 1400, max: 1600}}, csesBand: 3};
  let posts = [], fail = false;
  w.fetch = async (_url, opts = {}) => {
    if (opts.method === "PUT") {
      posts.push(JSON.parse(opts.body));
      if (fail) return {ok: false, status: 500};
      preferences = posts.at(-1);
      return {ok: true};
    }
    return {ok: true, json: async () => ({preferences, preferencesReady: true, signals: {}, linkedPlatforms: ["atcoder"],
      automatic: {codeforces: {difficulty: "cf:1500-1700", count: 3, why: "rated 1500"}}, suggest: {}})};
  };
  w.eval(fs.readFileSync(`${__dirname}/practice-levels.js`, "utf8"));
  await settle();
  const form = w.document.getElementById("practice-levels-form");
  assert.equal(form.querySelectorAll(".practice-level-card").length, 4);
  assert.equal(form.querySelectorAll(".practice-level-card a").length, 0);
  const atcoder = [...form.querySelectorAll(".practice-level-card")].find(card => card.querySelector("h3").textContent === "AtCoder");
  assert.match(atcoder.textContent, /Handle linked/);
  assert.doesNotMatch(atcoder.textContent, /Link your handle/);
  assert.doesNotMatch(form.textContent, /CodeChef|Kattis|CSES estimates use/);
  assert.equal(form.elements["codeforces-mode"].value, "custom");
  assert.equal(form.elements.cses.value, "3");
  form.elements.cses.value = "4";
  form.elements.cses.dispatchEvent(new w.Event("input", {bubbles: true}));
  await w.cosinePracticeLevels.load();
  assert.equal(form.elements.cses.value, "4", "stats refresh never overwrites an unsaved choice");
  form.elements["codeforces-min"].value = "1800";
  form.dispatchEvent(new w.Event("submit", {bubbles: true, cancelable: true}));
  await settle(); assert.equal(posts.length, 0, "invalid reversed range is not saved");
  form.elements["codeforces-max"].value = "2000";
  form.dispatchEvent(new w.Event("submit", {bubbles: true, cancelable: true}));
  await settle();
  assert.deepEqual(posts[0], {levels: {codeforces: {min: 1800, max: 2000}}, csesBand: 4});
  form.elements.cses.value = "5";
  w.document.getElementById("practice-level-auto").click();
  assert.equal(form.elements.cses.value, "5", "using profile heuristics keeps the currently chosen CSES band");
  assert.equal(form.elements["codeforces-mode"].value, "auto");
  form.dispatchEvent(new w.Event("submit", {cancelable: true})); await settle();
  assert.deepEqual(posts.at(-1), {levels: {}, csesBand: 5});
  fail = true;
  form.elements.cses.value = "2";
  form.elements.cses.dispatchEvent(new w.Event("input", {bubbles: true}));
  form.dispatchEvent(new w.Event("submit", {cancelable: true})); await settle();
  assert.equal(form.elements.cses.value, "2");
  assert.match(w.document.getElementById("practice-level-status").textContent, /Could not save/);
  assert.equal(w.document.getElementById("practice-level-save").disabled, false);
  dom.window.close();
  console.log("practice preferences DOM tests passed (overrides, validation, save, refresh race, failure retention)");
})().catch(error => {console.error(error); process.exitCode = 1;});
