const express = require("express");
const db = require("../db");
const { requireUser } = require("../auth/middleware");
const { validateLevels, practiceLevels } = require("../search/practice_levels");

const PLATFORMS = ["leetcode", "codeforces", "codechef", "github", "atcoder"];
// Each activity source belongs to a category; the client composes the
// dsa / dev / overall heatmap views from these. "algolens" = done-marks here.
const CATEGORIES = {
  leetcode: "dsa",
  codeforces: "dsa",
  codechef: "dsa",
  atcoder: "dsa",
  algolens: "dsa",
  github: "dev",
};
const HANDLE_RE = /^[A-Za-z0-9_.-]{1,64}$/;
// External stats are cached in user_platform_stats; a row older than the TTL
// is refetched. ?refresh=1 shrinks the TTL to a floor so the button works but
// can't hammer the upstream APIs.
const secrets = require("../crypto/secrets");

const TTL_MS = 12 * 60 * 60 * 1000;
const REFRESH_FLOOR_MS = 10 * 60 * 1000;
const DAY_SECONDS = 86400;
const HEATMAP_WINDOW_DAYS = 371; // 53 weeks

async function loadHandles(userId) {
  const result = await db.query(
    `SELECT platform, handle FROM user_platform_handles WHERE user_id = $1`,
    [userId]
  );
  const handles = {};
  // Rows written before encryption shipped come back without the version
  // prefix and decrypt to themselves, so this needs no backfill to work.
  for (const row of result.rows) handles[row.platform] = secrets.decrypt(row.handle);
  return handles;
}

function createProfileRouter({ fetchStats = require("../profile").fetchPlatformStats, problems = [] } = {}) {
  const router = express.Router();

  router.put("/preferences/practice-levels", requireUser, async (req, res) => {
    const { levels, csesBand } = req.body || {};
    if (!validateLevels(levels) || (csesBand !== null && (!Number.isInteger(csesBand) || csesBand < 1 || csesBand > 5))) {
      return res.status(400).json({error: "bad_practice_levels"});
    }
    try {
      await db.query(
        `INSERT INTO user_preferences (user_id, practice_levels, cses_band) VALUES ($1, $2::jsonb, $3)
         ON CONFLICT (user_id) DO UPDATE SET practice_levels = EXCLUDED.practice_levels,
         cses_band = EXCLUDED.cses_band, updated_at = NOW()`,
        [req.user.id, JSON.stringify(levels), csesBand]
      );
      res.set("Cache-Control", "no-store").json({levels, csesBand});
    } catch (err) {
      res.status(err.code === "42703" ? 503 : 500).json({error: err.code === "42703" ? "preferences_not_ready" : "db_error"});
    }
  });

  router.get("/preferences/cses-level", requireUser, async (req, res) => {
    try {
      const result = await db.query("SELECT cses_band FROM user_preferences WHERE user_id = $1", [req.user.id]);
      res.set("Cache-Control", "no-store");
      res.json({ band: result.rows[0]?.cses_band ?? null });
    } catch (_err) { res.status(500).json({ error: "db_error" }); }
  });

  router.put("/preferences/cses-level", requireUser, async (req, res) => {
    const band = req.body?.band;
    if (band !== null && (!Number.isInteger(band) || band < 1 || band > 5)) {
      return res.status(400).json({ error: "bad_cses_band" });
    }
    try {
      await db.query(
        `INSERT INTO user_preferences (user_id, cses_band) VALUES ($1, $2)
         ON CONFLICT (user_id) DO UPDATE SET cses_band = EXCLUDED.cses_band, updated_at = NOW()`,
        [req.user.id, band]
      );
      res.set("Cache-Control", "no-store");
      res.json({ band });
    } catch (_err) { res.status(500).json({ error: "db_error" }); }
  });

  // Whether technique labels are shown before you attempt a problem. Default
  // is hidden, so `null` ("never chose") and `false` behave the same today —
  // they are stored apart so the default can move without rewriting choices.
  router.get("/preferences/show-labels", requireUser, async (req, res) => {
    res.set("Cache-Control", "no-store");
    try {
      const result = await db.query("SELECT show_labels FROM user_preferences WHERE user_id = $1", [req.user.id]);
      res.json({ showLabels: result.rows[0]?.show_labels ?? null });
    } catch (_err) {
      // A deploy can land minutes before its migration, and then this column
      // does not exist. "Never chose" is the honest answer in that window; a
      // 500 would make the search page report an error about a preference
      // nobody has set.
      res.json({ showLabels: null });
    }
  });

  router.put("/preferences/show-labels", requireUser, async (req, res) => {
    const showLabels = req.body?.showLabels;
    if (typeof showLabels !== "boolean") {
      return res.status(400).json({ error: "bad_show_labels" });
    }
    try {
      await db.query(
        `INSERT INTO user_preferences (user_id, show_labels) VALUES ($1, $2)
         ON CONFLICT (user_id) DO UPDATE SET show_labels = EXCLUDED.show_labels, updated_at = NOW()`,
        [req.user.id, showLabels]
      );
      res.set("Cache-Control", "no-store");
      res.json({ showLabels });
    } catch (_err) { res.status(500).json({ error: "db_error" }); }
  });

  // What the search page needs to offer "at my level", and nothing else.
  //
  // Deliberately cache-only: it reads whatever /profile already stored and
  // never calls out to a judge. The search page loads on every visit, and a
  // filter button is not worth five external round-trips — if the numbers are
  // stale or absent, the button simply doesn't appear until the profile page
  // has been opened once.
  router.get("/level", requireUser, async (req, res) => {
    try {
      const [cached, preferences] = await Promise.all([
        db.query(`SELECT platform, payload, fetched_at FROM user_platform_stats WHERE user_id = $1`, [req.user.id]),
        db.query("SELECT cses_band, practice_levels FROM user_preferences WHERE user_id = $1", [req.user.id])
          .catch(async err => {
            if (err.code !== "42703") throw err;
            const legacy = await db.query("SELECT cses_band FROM user_preferences WHERE user_id = $1", [req.user.id]);
            return {...legacy, preferencesReady: false};
          }),
      ]);
      const signals = {};
      if (preferences.rows[0]?.cses_band != null) signals.cses = { band: preferences.rows[0].cses_band };
      for (const row of cached.rows) {
        const stats = secrets.decryptJson(row.payload);
        if (!stats || stats.unavailable) continue;
        const signal = { fetchedAt: row.fetched_at };
        if (typeof stats.rating === "number") signal.rating = stats.rating;
        if (stats.byDifficulty) signal.byDifficulty = stats.byDifficulty;
        if (signal.rating !== undefined || signal.byDifficulty) signals[row.platform] = signal;
      }
      res.set("Cache-Control", "no-store");
      const levels = preferences.rows[0]?.practice_levels || {};
      res.json({ signals, ...practiceLevels(signals, levels, problems), preferences: {
        levels, csesBand: preferences.rows[0]?.cses_band ?? null,
      }, preferencesReady: preferences.preferencesReady !== false });
    } catch (_err) {
      res.status(500).json({ error: "db_error" });
    }
  });

  router.get("/handles", requireUser, async (req, res) => {
    try {
      res.json({ handles: await loadHandles(req.user.id) });
    } catch (_err) {
      res.status(500).json({ error: "db_error" });
    }
  });

  // Body: { leetcode?, codeforces?, codechef? } — empty string deletes the
  // handle. Any handle change drops the cached stats row (cache is keyed to
  // the handle's identity, not just the platform).
  router.put("/handles", requireUser, async (req, res) => {
    const body = req.body || {};
    const changes = [];
    for (const platform of PLATFORMS) {
      if (!(platform in body)) continue;
      if (typeof body[platform] !== "string") {
        return res.status(400).json({ error: "bad_handle" });
      }
      const handle = body[platform].trim();
      if (handle && !HANDLE_RE.test(handle)) {
        return res.status(400).json({ error: "bad_handle" });
      }
      changes.push({ platform, handle });
    }
    try {
      for (const { platform, handle } of changes) {
        if (handle) {
          await db.query(
            `INSERT INTO user_platform_handles (user_id, platform, handle)
             VALUES ($1, $2, $3)
             ON CONFLICT (user_id, platform)
             DO UPDATE SET handle = EXCLUDED.handle, updated_at = NOW()`,
            [req.user.id, platform, secrets.encrypt(handle)]
          );
        } else {
          await db.query(
            `DELETE FROM user_platform_handles WHERE user_id = $1 AND platform = $2`,
            [req.user.id, platform]
          );
        }
        await db.query(
          `DELETE FROM user_platform_stats WHERE user_id = $1 AND platform = $2`,
          [req.user.id, platform]
        );
      }
      res.json({ ok: true, handles: await loadHandles(req.user.id) });
    } catch (_err) {
      res.status(500).json({ error: "db_error" });
    }
  });

  router.get("/profile", requireUser, async (req, res) => {
    const wantRefresh = req.query.refresh === "1";
    const maxAgeMs = wantRefresh ? REFRESH_FLOOR_MS : TTL_MS;
    try {
      // The three reads are independent — one Neon round-trip instead of a
      // sequential waterfall (matters: Render↔Neon is a cross-region hop).
      const [handles, cached, doneRows] = await Promise.all([
        loadHandles(req.user.id),
        db.query(
          `SELECT platform, payload, fetched_at FROM user_platform_stats WHERE user_id = $1`,
          [req.user.id]
        ),
        db.query(
          `SELECT done_at FROM user_problem_state WHERE user_id = $1 AND done AND done_at IS NOT NULL`,
          [req.user.id]
        ),
      ]);
      const cacheByPlatform = new Map(cached.rows.map((r) => [r.platform, r]));

      const platforms = {};
      await Promise.all(
        Object.entries(handles).map(async ([platform, handle]) => {
          const row = cacheByPlatform.get(platform);
          const age = row ? Date.now() - new Date(row.fetched_at).getTime() : Infinity;
          if (row && age < maxAgeMs) {
            platforms[platform] = { ...secrets.decryptJson(row.payload), fetchedAt: row.fetched_at };
            return;
          }
          const payload = await fetchStats(platform, handle);
          if (payload.unavailable && row) {
            // stale-if-error: keep serving the last good numbers
            platforms[platform] = { ...secrets.decryptJson(row.payload), fetchedAt: row.fetched_at, stale: true };
            return;
          }
          await db.query(
            `INSERT INTO user_platform_stats (user_id, platform, payload, fetched_at)
             VALUES ($1, $2, $3, NOW())
             ON CONFLICT (user_id, platform)
             DO UPDATE SET payload = EXCLUDED.payload, fetched_at = NOW()`,
            [req.user.id, platform, JSON.stringify(secrets.encryptJson(payload))]
          );
          platforms[platform] = { ...payload, fetchedAt: new Date().toISOString() };
        })
      );

      // The client composes the dsa / dev / overall heatmap views from the
      // per-platform calendars (already in platforms.*.calendar) plus this
      // AlgoLens done-marks calendar — no server-side pre-merge, so tab
      // switches cost zero network and the payload carries each day once.
      const cutoff = Math.floor(Date.now() / 1000 / DAY_SECONDS - HEATMAP_WINDOW_DAYS) * DAY_SECONDS;
      const algolensCalendar = {};
      for (const row of doneRows.rows) {
        const daySec = Math.floor(new Date(row.done_at).getTime() / 1000 / DAY_SECONDS) * DAY_SECONDS;
        if (daySec >= cutoff) {
          algolensCalendar[String(daySec)] = (algolensCalendar[String(daySec)] || 0) + 1;
        }
      }

      const totalSolved = Object.values(platforms).reduce(
        (sum, s) => sum + (typeof s.solved === "number" ? s.solved : 0),
        0
      );
      // Browser may reuse this for a minute (per user; ?refresh=1 is a
      // different URL and always revalidates). Stats are 12h-cached anyway.
      if (!wantRefresh) res.set("Cache-Control", "private, max-age=60");
      res.json({
        handles,
        platforms,
        combined: {
          totalSolved,
          algolensDone: doneRows.rows.length,
          categories: CATEGORIES,
          calendars: { algolens: algolensCalendar },
        },
      });
    } catch (_err) {
      res.status(500).json({ error: "db_error" });
    }
  });

  return router;
}

module.exports = { createProfileRouter };
