// Account preferences on Profile. No extra upstream calls: /api/level only
// reads cached stats, with explicit manual overrides returned separately.
(() => {
  const form = document.getElementById("practice-levels-form");
  if (!form) return;
  const grid = document.getElementById("practice-level-grid");
  const status = document.getElementById("practice-level-status");
  const save = document.getElementById("practice-level-save");
  const auto = document.getElementById("practice-level-auto");
  const names = {codeforces: "Codeforces", atcoder: "AtCoder", leetcode: "LeetCode", cses: "CSES"};
  const bands = ["Foundation", "Standard", "Intermediate", "Advanced", "Expert"];
  let data = null, dirty = false, saving = false, requestId = 0;

  function element(tag, text, parent) {
    const el = document.createElement(tag);
    if (text != null) el.textContent = text;
    if (parent) parent.appendChild(el);
    return el;
  }
  function select(parent, name, choices, value) {
    const el = element("select", null, parent);
    el.name = name;
    for (const [id, text] of choices) {
      const opt = element("option", text, el); opt.value = id;
    }
    el.value = value;
    return el;
  }
  function paint() {
    grid.replaceChildren();
    for (const [judge, title] of Object.entries(names)) {
      const card = element("div", null, grid); card.className = "practice-level-card";
      element("h3", title, card);
      const choice = data.preferences.levels[judge];
      const suggestion = data.automatic[judge];
      const label = element("label", judge === "cses" ? "Starting band" : "Practice target", card);
      if (judge === "cses") {
        select(label, "cses", [["", "Not set"], ...bands.map((b, i) => [String(i + 1), b])], String(data.preferences.csesBand || ""));
        element("p", "CSES estimates use their own scale. Choose a starting band; CF and AtCoder ratings are not converted into CSES levels.", card);
      } else {
        const mode = select(label, `${judge}-mode`, [["auto", "From my profile"], ["custom", "Choose my own"]], choice ? "custom" : "auto");
        const fields = element("div", null, card);
        fields.hidden = !choice;
        if (judge === "leetcode") {
          select(element("label", "Tier", fields), "leetcode-tier", [["easy", "Easy"], ["medium", "Medium"], ["hard", "Hard"]], choice?.tier || "medium");
        } else {
          // Defaults are suggestions where available, never an inferred rating
          // from another platform. Both edges remain editable.
          const range = /:(-?\d+)-(-?\d+)/.exec(suggestion?.difficulty || "");
          for (const edge of ["min", "max"]) {
            const input = element("input", null, element("label", edge === "min" ? "From" : "To", fields));
            input.type = "number"; input.name = `${judge}-${edge}`; input.step = "1";
            input.min = judge === "atcoder" ? "-1000" : "0"; input.max = "5000";
            input.value = choice?.[edge] ?? (range ? Number(range[edge === "min" ? 1 : 2]) : edge === "min" ? 800 : 1000);
            input.required = true; input.disabled = !choice;
          }
        }
        mode.addEventListener("change", () => {
          fields.hidden = mode.value !== "custom";
          fields.querySelectorAll("input").forEach(el => { el.disabled = fields.hidden; });
        });
        element("p", suggestion
          ? `Profile suggestion: ${suggestion.difficulty} · ${suggestion.why} · ${suggestion.count} problems`
          : "No profile suggestion yet. Link your handle below and refresh stats, or choose your own target.", card);
        const stamp = data.signals?.[judge]?.fetchedAt;
        if (stamp) element("p", `Stats as of ${new Date(stamp).toLocaleDateString()}`, card);
      }
      const effective = data.suggest[judge];
      if (effective) {
        const link = element("a", `Practice saved ${title} level ↗`, card);
        link.href = `/?platform=${encodeURIComponent(judge)}&difficulty=${encodeURIComponent(effective.difficulty)}`;
      }
    }
    const unsupported = element("div", null, grid); unsupported.className = "practice-level-card";
    element("h3", "CodeChef & Kattis", unsupported);
    element("p", "Browse these judges normally. This corpus does not yet have compatible difficulty filters for a reliable “my level” target. We do not translate another judge’s rating into one.", unsupported);
    const ready = data.preferencesReady !== false;
    save.disabled = auto.disabled = !ready;
    status.textContent = ready ? "Saved to your account. Resetting search will keep these preferences." : "Preferences are read-only until the practice-level database migration is applied.";
    grid.querySelectorAll("input, select").forEach(el => { if (!ready) el.disabled = true; });
  }

  async function load() {
    if (dirty || saving) return;
    const request = ++requestId;
    try {
      const res = await fetch("/api/level");
      if (!res.ok) throw new Error(res.status === 401 ? "Sign in to set practice levels." : "Could not load practice levels. Reload to retry.");
      const next = await res.json();
      if (request !== requestId || dirty || saving) return;
      data = next;
      paint();
    } catch (err) { if (request === requestId && !dirty) status.textContent = err.message; }
  }

  form.addEventListener("input", () => { dirty = true; status.textContent = "Unsaved changes — save to update “my level” in search."; });
  form.addEventListener("change", () => { dirty = true; });
  auto.addEventListener("click", () => {
    data.preferences = {levels: {}, csesBand: form.elements.cses.value ? Number(form.elements.cses.value) : null};
    paint(); dirty = true;
    status.textContent = "Profile suggestions selected. Your CSES band is kept because it has no automatic estimate. Press save to apply.";
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (saving || !data || data.preferencesReady === false || !form.reportValidity()) return;
    const values = new FormData(form);
    const levels = {};
    for (const judge of ["codeforces", "atcoder", "leetcode"]) {
      if (values.get(`${judge}-mode`) !== "custom") continue;
      if (judge === "leetcode") levels[judge] = {tier: values.get("leetcode-tier")};
      else {
        const min = Number(values.get(`${judge}-min`)), max = Number(values.get(`${judge}-max`));
        if (min > max) { status.textContent = `${names[judge]}: “From” must not exceed “To”.`; return; }
        levels[judge] = {min, max};
      }
    }
    const csesBand = values.get("cses") ? Number(values.get("cses")) : null;
    saving = true; ++requestId;
    const controls = [...form.querySelectorAll("input, select, button")];
    const disabled = controls.map(el => el.disabled);
    controls.forEach(el => { el.disabled = true; });
    status.textContent = "Saving…";
    try {
      const res = await fetch("/api/preferences/practice-levels", {method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify({levels, csesBand})});
      if (!res.ok) throw new Error(res.status === 503 ? "Preferences are not ready yet. Your choices have not been saved." : "Could not save. Your choices are still here; try again.");
      dirty = false;
      data.preferences = {levels, csesBand};
      status.textContent = "Practice levels saved.";
    } catch (err) { status.textContent = err.message; }
    finally { saving = false; controls.forEach((el, i) => { el.disabled = disabled[i]; }); }
    if (!dirty) await load();
  });
  window.addEventListener("beforeunload", event => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
  window.cosinePracticeLevels = {load};
  load();
})();
