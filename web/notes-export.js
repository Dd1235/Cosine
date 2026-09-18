// Notes stay in the browser. The server supplies only the same problem list
// used by the current view; note text and custom cells never leave the device.
(() => {
  const panel = document.getElementById("notes-export");
  const status = document.getElementById("notes-export-status");
  let source = null, controller = null, preview = null, busy = false;

  function invalidate() {
    source = null;
    controller?.abort();
    if (preview && !preview.closed) preview.close();
    preview = null;
    if (panel) panel.hidden = true;
  }

  function setSource(next) {
    invalidate();
    if (!next.userId) return;
    source = {...next, hits: [...next.hits], viewUrl: location.href};
    if (panel) panel.hidden = false;
    if (status) status.textContent = "";
  }

  async function collect(selected, fetchImpl, signal) {
    if (selected.complete) return selected.hits;
    // The API accepts up to the corpus size. Keep every facet and ranking
    // parameter from the successful on-screen request; reset only pagination.
    const url = new URL(selected.url, location.origin);
    url.searchParams.set("offset", "0");
    url.searchParams.set("k", String(Math.max(1, selected.total || 1)));
    const response = await fetchImpl(url.pathname + url.search, {signal});
    if (!response.ok) throw new Error(`Could not load all results (${response.status}). Retry the export.`);
    const data = await response.json();
    if (!Array.isArray(data.hits) || !Number.isInteger(data.total) || data.hits.length < data.total) {
      throw new Error("The result list changed or was incomplete. Refresh this view and retry the export.");
    }
    const offset = Number(new URL(selected.url, location.origin).searchParams.get("offset")) || 0;
    if ((selected.hits || []).some((hit, i) => hit.problem.id !== data.hits[offset + i]?.problem?.id)) {
      throw new Error("The result order changed. Refresh this view and retry the export.");
    }
    return data.hits;
  }

  function snapshot(hits, sheets, selected, includeEmpty, difficulty) {
    const seen = new Set();
    let rows = [];
    for (const hit of hits) {
      const problem = hit?.problem;
      if (!problem?.id || seen.has(problem.id)) continue;
      seen.add(problem.id);
      const fields = sheets.noteFields(problem.id).map(c => ({label: c.label, value: String(c.value ?? "")}))
        .filter(c => c.value.trim());
      if (selected.notesFilter && (selected.notesFilter === "yes") !== !!fields.length) continue;
      rows.push({problem: {...problem}, fields, pending: sheets.hasPendingNote(problem.id), done: !!hit.done,
        bookmarked: !!hit.bookmarked, recall: hit.recall || "", difficulty: difficulty.format(problem)});
    }
    if (selected.clientSort) {
      rows = rows.slice(0, selected.clientSort.limit).sort((a, b) => {
        const av = difficulty.value(a.problem), bv = difficulty.value(b.problem);
        if (av == null || bv == null) return av == null ? (bv == null ? 0 : 1) : -1;
        return selected.clientSort.direction === "desc" ? bv - av : av - bv;
      });
    }
    const matched = rows.length;
    if (!includeEmpty) rows = rows.filter(r => r.fields.length);
    return {rows, matched, skipped: matched - rows.length, context: selected.context,
      viewUrl: selected.viewUrl, createdAt: new Date().toISOString()};
  }

  const css = `
    :root { color-scheme: light; }
    body { max-width: 850px; margin: 2rem auto; padding: 0 1.25rem; color: #18222c; background: #fff; font: 16px/1.6 system-ui, sans-serif; overflow-wrap: anywhere; }
    h1 { font-size: 1.65rem; } h2 { font-size: 1.25rem; margin-bottom: .25rem; } h3 { font-size: .85rem; color: #42566b; margin-bottom: .35rem; }
    a { color: #23547b; } .meta { color: #526272; font-size: .85rem; } article { border-top: 1px solid #ccd5df; padding-top: .75rem; margin-top: 1.5rem; }
    .note-para { display: block; white-space: pre-wrap; margin: .35rem 0; } .note-heading { display: block; margin: .85rem 0 .3rem; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; tab-size: 4; border: 1px solid #dce2e8; background: #f5f7fa; padding: .8rem; font-size: .85rem; }
    code { white-space: pre-wrap; font-size: .9em; } .note-list { padding-left: 1.5rem; } .formula-fallback { white-space: pre-wrap; font-family: monospace; }
    math[display="block"] { display: block; margin: .8rem 0; max-width: 100%; overflow-x: auto; }
    .toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #ccd5df; }
    button { font: inherit; padding: .45rem .8rem; cursor: pointer; } .notice { padding: .75rem; background: #fff5d9; }
    @page { margin: 16mm; }
    @media print { body { margin: 0; padding: 0; max-width: none; font-size: 10pt; } .toolbar { display: none; } h2,h3,.note-heading { break-after: avoid; } pre,li,math { break-inside: avoid; } p { orphans: 3; widows: 3; } a { color: inherit; text-decoration: none; } }
  `;

  function safeUrl(raw) {
    try { const url = new URL(raw); return ["http:", "https:"].includes(url.protocol) ? url.href : ""; }
    catch (_) { return ""; }
  }

  function html(plan, renderMarkdown, math) {
    const doc = document.implementation.createHTMLDocument("cosine · exported notes");
    doc.documentElement.lang = "en";
    const charset = doc.createElement("meta"); charset.setAttribute("charset", "utf-8"); doc.head.prepend(charset);
    const viewport = doc.createElement("meta"); viewport.name = "viewport"; viewport.content = "width=device-width, initial-scale=1"; doc.head.appendChild(viewport);
    const style = doc.createElement("style"); style.textContent = css; doc.head.appendChild(style);
    function add(tag, text, parent = doc.body, className = "") {
      const el = doc.createElement(tag); el.textContent = text; el.className = className; parent.appendChild(el); return el;
    }
    const toolbar = add("div", "", doc.body, "toolbar");
    const print = add("button", "Print / Save as PDF", toolbar); print.id = "print-notes";
    add("span", "Choose Save as PDF in your browser’s print dialog.", toolbar, "meta");
    add("h1", "Practice notes");
    add("p", `${plan.rows.length} problems · ${plan.skipped} empty entries skipped · ${new Date(plan.createdAt).toLocaleString()}`, doc.body, "meta");
    add("p", plan.context || "Current view", doc.body, "meta");
    add("p", `View: ${plan.viewUrl}`, doc.body, "meta");
    add("p", "Includes locally saved edits and custom columns available at export time.", doc.body, "meta");
    let formulasAsText = 0;
    const renderMath = (formula, displayMode) => {
      const el = doc.createElement("span");
      try {
        if (!math) throw new Error("Math unavailable");
        // Native MathML keeps the file self-contained, with no remote scripts,
        // stylesheets, or fonts needed when reopened offline or printed.
        math.render(formula, el, {displayMode, output: "mathml", trust: false, throwOnError: true,
          strict: "ignore", maxExpand: 200, maxSize: 10, macros: {}});
      } catch (_) {
        formulasAsText++;
        el.className = "formula-fallback";
        el.textContent = displayMode ? `$$\n${formula}\n$$` : `$${formula}$`;
      }
      return el;
    };
    for (const [i, row] of plan.rows.entries()) {
      const article = add("article", "");
      const title = add("h2", `${i + 1}. ${row.problem.title || row.problem.id}`, article);
      const url = safeUrl(row.problem.url);
      if (url) { const link = doc.createElement("a"); link.href = url; link.textContent = title.textContent; title.replaceChildren(link); }
      add("p", [row.problem.platform, row.difficulty, row.problem.id,
        row.done ? "done" : "", row.bookmarked ? "bookmarked" : "", row.recall ? `recall: ${row.recall}` : ""].filter(Boolean).join(" · "), article, "meta");
      if (row.pending) add("p", "Includes local edits not yet synced to your sheet.", article, "meta");
      if (!row.fields.length) add("p", "No notes or custom-column content.", article, "meta");
      for (const field of row.fields) {
        add("h3", field.label, article);
        article.appendChild(doc.importNode(renderMarkdown(field.value, renderMath), true));
      }
    }
    if (formulasAsText) add("p", `${formulasAsText} formulas could not be rendered and are preserved as LaTeX text.`, doc.body, "notice");
    const script = doc.createElement("script");
    script.textContent = 'document.getElementById("print-notes").addEventListener("click",function(){window.print()});';
    doc.body.appendChild(script);
    return {text: "<!doctype html>\n" + doc.documentElement.outerHTML, formulasAsText};
  }

  function markdown(plan) {
    const literal = value => String(value ?? "").replace(/[\\`*_{}\[\]()<>#+.!|~$-]/g, "\\$&").replace(/\r?\n/g, " ");
    const lines = ["# Practice notes", "", `${plan.rows.length} problems · ${plan.skipped} empty entries skipped`, "",
      literal(plan.context), "", `Exported: ${plan.createdAt}`, "", `View: ${literal(plan.viewUrl)}`, ""];
    for (const [i, row] of plan.rows.entries()) {
      lines.push(`## ${i + 1}. ${literal(row.problem.title || row.problem.id)}`, "");
      const url = safeUrl(row.problem.url);
      if (url) lines.push(`[Open problem](<${url.replace(/>/g, "%3E").replace(/</g, "%3C")}>)`, "");
      lines.push(literal([row.problem.platform, row.difficulty, row.problem.id].filter(Boolean).join(" · ")), "");
      if (row.pending) lines.push("Includes local edits not yet synced to your sheet.", "");
      if (!row.fields.length) lines.push("No notes or custom-column content.", "");
      for (const field of row.fields) lines.push(`### ${literal(field.label)}`, "", field.value, "");
      lines.push("---", "");
    }
    return lines.join("\n");
  }

  function download(text, extension, type) {
    const url = URL.createObjectURL(new Blob([text], {type}));
    const link = document.createElement("a"); link.href = url;
    link.download = `cosine-notes-${new Date().toISOString().slice(0, 10)}.${extension}`;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  async function start(format) {
    if (busy || !source) return;
    const selected = source;
    busy = true;
    controller = new AbortController();
    const abort = controller;
    const timeout = setTimeout(() => abort.abort(), 30000);
    const buttons = [...panel.querySelectorAll("button")]; buttons.forEach(b => { b.disabled = true; });
    try {
      if (format === "print") {
        preview = window.open("", "_blank");
        if (!preview) throw new Error("Allow pop-ups for the PDF preview, or download HTML and print it after opening.");
        preview.opener = null;
        preview.document.body.textContent = "Preparing your notes…";
      }
      status.textContent = "Preparing all matching notes…";
      const hits = await collect(selected, fetch, abort.signal);
      if (selected !== source || abort.signal.aborted) throw new Error("Export cancelled. Retry from the current view.");
      const plan = snapshot(hits, cosineSheets, selected, document.getElementById("export-empty").checked, cosineDifficulty);
      if (!plan.rows.length) throw new Error(plan.matched
        ? "No notes or custom-column content matches. Enable ‘include empty problems’ to export the problem list."
        : "No problems match this view’s filters.");
      let warning = "";
      if (format === "markdown") download(markdown(plan), "md", "text/markdown;charset=utf-8");
      else {
        const needsMath = plan.rows.some(row => row.fields.some(f => f.value.includes("$")));
        let math;
        if (needsMath) {
          // A missing math asset must not hang export or discard formulas.
          let mathTimer;
          try { math = await Promise.race([globalThis.loadNoteMath(), new Promise(resolve => { mathTimer = setTimeout(resolve, 8000); })]); }
          catch (_) {} finally { clearTimeout(mathTimer); }
        }
        if (selected !== source || abort.signal.aborted) throw new Error("Export cancelled. Retry from the current view.");
        const result = html(plan, globalThis.renderNoteMarkdown, math);
        if (format === "print") {
          if (!preview || preview.closed) throw new Error("The preview was closed. Retry the export.");
          preview.document.open(); preview.document.write(result.text); preview.document.close();
          preview = null; // completed previews belong to the user
        } else download(result.text, "html", "text/html;charset=utf-8");
        if (result.formulasAsText) warning = ` ${result.formulasAsText} formulas were preserved as LaTeX text.`;
      }
      status.textContent = `${plan.rows.length} problems exported · ${plan.skipped} empty entries skipped.${warning}`;
    } catch (err) {
      if (preview && !preview.closed) preview.close();
      preview = null;
      if (selected === source) status.textContent = err.name === "AbortError" ? "Export timed out. Please retry." : err.message;
    } finally {
      clearTimeout(timeout); busy = false; buttons.forEach(b => { b.disabled = false; });
      if (controller === abort) controller = null;
    }
  }

  if (panel) panel.querySelectorAll("[data-notes-export]").forEach(button => button.addEventListener("click", () => start(button.dataset.notesExport)));
  window.addEventListener("pagehide", invalidate);
  globalThis.cosineNotesExport = {invalidate, setSource, collect, snapshot, html, markdown, start};
})();
