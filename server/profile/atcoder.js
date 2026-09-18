// Independent sources: a slow community submissions API must not discard an
// available official rating (or vice versa).

const SUBMISSIONS_URL = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions";
const HISTORY_URL = (handle) => `https://atcoder.jp/users/${encodeURIComponent(handle)}/history/json`;
const PAGE_LIMIT = 10; // the API returns ≤500 rows per call; cap the walk like CF
const WINDOW_DAYS = 371; // one heatmap window; older submissions aren't rendered

async function fetchAtCoder(handle, { fetchImpl, timeoutMs }) {
  const { dayBucket, errorWithCode, DAY_SECONDS } = require("./index");

  // Resolve partial results before the outer platform deadline. Each budget
  // covers the whole source, including pagination and response body decoding.
  async function source(work) {
    const controller = new AbortController();
    let timer;
    const deadline = new Promise((_, reject) => {
      timer = setTimeout(() => {
        controller.abort();
        reject(Object.assign(new Error("AtCoder source timeout"), {name: "AbortError"}));
      }, Math.max(1, Math.floor(timeoutMs * 0.8)));
    });
    const get = url => {
      controller.signal.throwIfAborted();
      return fetchImpl(url, {signal: controller.signal, headers: {"user-agent": "Mozilla/5.0 (cosine profile)"}});
    };
    try { return await Promise.race([work(get), deadline]); }
    finally { clearTimeout(timer); }
  }

  const [activity, history] = await Promise.allSettled([
    source(async get => {
      let from = Math.floor(Date.now() / 1000) - WINDOW_DAYS * DAY_SECONDS;
      const solved = new Set(), calendar = {};
      for (let page = 0; page < PAGE_LIMIT; page += 1) {
        const url = `${SUBMISSIONS_URL}?user=${encodeURIComponent(handle)}&from_second=${from}`;
        const res = await get(url);
        if (!res.ok) throw errorWithCode(`atcoder http ${res.status}`, "PARSE_FAILED");
        const batch = await res.json();
        if (!Array.isArray(batch)) throw errorWithCode("atcoder unexpected payload", "PARSE_FAILED");
        for (const sub of batch) {
          if (!Number.isFinite(sub.epoch_second)) continue;
          const key = dayBucket(sub.epoch_second);
          calendar[key] = (calendar[key] || 0) + 1;
          if (sub.result === "AC" && sub.problem_id) solved.add(sub.problem_id);
        }
        if (batch.length < 500) break;
        // Walk forward from the newest row; +1s so the page cannot repeat.
        from = Math.max(...batch.map(s => s.epoch_second || 0)) + 1;
      }
      return { solved: solved.size, calendar };
    }),
    source(async get => {
      const res = await get(HISTORY_URL(handle));
      if (res.status === 404) throw errorWithCode("atcoder user not found", "NOT_FOUND");
      if (!res.ok) throw errorWithCode(`atcoder history http ${res.status}`, "PARSE_FAILED");
      const contests = await res.json();
      if (!Array.isArray(contests)) throw errorWithCode("atcoder unexpected history", "PARSE_FAILED");
      // Unrated appearances must not replace the latest actual contest rating.
      const rated = contests.filter(c => c.IsRated !== false && Number.isFinite(c.NewRating));
      return {rating: rated.at(-1)?.NewRating ?? null, ratingState: rated.length ? "rated" : "unrated"};
    }),
  ]);
  if (history.status === "rejected" && history.reason?.code === "NOT_FOUND") throw history.reason;
  if (activity.status === "rejected" && history.status === "rejected") throw history.reason;
  return {
    ...(activity.status === "fulfilled" ? activity.value : {solved: null, calendar: {}}),
    ...(history.status === "fulfilled" ? history.value : {rating: null, ratingState: "unavailable"}),
    partial: activity.status === "rejected" || history.status === "rejected",
  };
}

module.exports = { fetchAtCoder };
