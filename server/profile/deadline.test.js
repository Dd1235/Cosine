const assert = require("node:assert/strict");
const { fetchPlatformStats } = require("./index");

(async () => {
  let signal;
  const started = Date.now();
  const stalledBody = await fetchPlatformStats("codeforces", "test", {
    timeoutMs: 40,
    fetchImpl: async (_url, options) => {
      signal = options.signal;
      return {ok: true, json: () => new Promise(() => {})};
    },
  });
  assert.equal(stalledBody.error, "timeout", "deadline includes reading response body");
  assert.equal(signal.aborted, true, "deadline aborts outstanding network work");
  assert.ok(Date.now() - started < 1000);

  let calls = 0;
  const sequential = await fetchPlatformStats("codeforces", "test", {
    timeoutMs: 70,
    fetchImpl: async (_url, {signal}) => {
      calls++;
      await new Promise((resolve, reject) => {
        const timer = setTimeout(resolve, 45);
        signal.addEventListener("abort", () => {
          clearTimeout(timer);
          reject(Object.assign(new Error("aborted"), {name: "AbortError"}));
        }, {once: true});
      });
      return {ok: true, json: async () => ({status: "OK", result: calls === 1 ? [{rating: 1500}] : []})};
    },
  });
  assert.equal(calls, 2);
  assert.equal(sequential.error, "timeout", "sequential calls share one deadline");
  for (const stalledSource of ["kenkoooo", "atcoder.jp"]) {
    let stalledSignal;
    const partial = await fetchPlatformStats("atcoder", "test", {
      timeoutMs: 100,
      fetchImpl: async (url, {signal}) => {
        if (url.includes(stalledSource)) {
          stalledSignal = signal;
          return {ok: true, json: () => new Promise(() => {})};
        }
        return {ok: true, json: async () => url.includes("atcoder.jp") ? [{NewRating: 1400}] : []};
      },
    });
    assert.equal(partial.unavailable, undefined, "one slow source does not discard the other");
    assert.equal(partial.partial, true);
    assert.equal(stalledSignal.aborted, true);
    if (stalledSource === "kenkoooo") assert.equal(partial.rating, 1400);
    else assert.equal(partial.solved, 0);
  }
  console.log("profile deadline tests passed");
})().catch(error => {console.error(error); process.exitCode = 1;});
