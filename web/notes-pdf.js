// Heavy PDF/font/math assets are requested only for a direct PDF download.
(() => {
  let loading;
  function script(src) {
    return new Promise((resolve, reject) => {
      const el = document.createElement("script");
      const timer = setTimeout(() => { el.remove(); reject(new Error("PDF assets timed out. Please retry.")); }, 30000);
      el.src = src;
      el.onload = () => { clearTimeout(timer); resolve(); };
      el.onerror = () => { clearTimeout(timer); el.remove(); reject(new Error("Could not load PDF assets. Please retry, or use print preview.")); };
      document.head.appendChild(el);
    });
  }
  function load() {
    if (!loading) loading = (async () => {
      if (!globalThis.pdfMake) await script("/vendor/pdfmake/pdfmake.min.js");
      await script("/vendor/pdfmake/vfs_fonts.js");
      globalThis.pdfMake.addFonts({Mono: {
        normal: location.origin + "/vendor/notes-mono.woff",
        bold: location.origin + "/vendor/notes-mono.woff",
        italics: location.origin + "/vendor/notes-mono.woff",
        bolditalics: location.origin + "/vendor/notes-mono.woff",
      }, Symbols: {
        normal: location.origin + "/vendor/notes-symbols.woff",
        bold: location.origin + "/vendor/notes-symbols.woff",
        italics: location.origin + "/vendor/notes-symbols.woff",
        bolditalics: location.origin + "/vendor/notes-symbols.woff",
      }});
      if (!globalThis.MathJax?.mathml2svg) {
        globalThis.MathJax = {startup: {typeset: false}, svg: {fontCache: "none"}};
        await script("/vendor/notes-math.js");
        await globalThis.MathJax.startup.promise;
      }
    })().catch(error => { loading = null; throw error; });
    return loading;
  }

  // Convert our safe note DOM, not arbitrary HTML. Formulas are vector blocks
  // (including inline formulas) so fractions and sums remain legible in PDF.
  function definition(html, mathToSvg) {
    const doc = new globalThis.DOMParser().parseFromString(html, "text/html");
    let formulasAsText = 0;
    function runs(value, style = {}) {
      return value.split(/([\u0370-\u03ff\u2190-\u22ff\u2308-\u230b\u27c0-\u27ef\u2980-\u2aff]+)/u).filter(Boolean)
        .map(text => ({text, ...style, ...(/^[\u0370-\u03ff\u2190-\u22ff\u2308-\u230b\u27c0-\u27ef\u2980-\u2aff]/u.test(text) ? {font: "Symbols"} : {})}));
    }
    function blocks(parent) {
      const result = [];
      let text = [];
      const flush = () => { if (text.length) result.push({text, margin: [0, 2, 0, 4]}); text = []; };
      function visit(node, style = {}) {
        if (node.nodeType === 3) { text.push(...runs(node.textContent, style)); return; }
        if (node.nodeType !== 1) return;
        const tag = node.tagName.toLowerCase();
        if (["script", "style", "button"].includes(tag) || node.classList.contains("toolbar")) return;
        if (tag === "math") {
          flush();
          try {
            const svg = mathToSvg(node.outerHTML);
            const box = svg.getAttribute("viewBox").split(/\s+/).map(Number);
            const width = Math.min(480, Math.max(1, box[2] / 1000 * 11));
            const height = width * box[3] / box[2];
            if (!Number.isFinite(height) || height <= 0 || height > 680) throw new Error("Oversized formula");
            svg.setAttribute("width", String(width)); svg.setAttribute("height", String(height));
            result.push({svg: svg.outerHTML, width, margin: [0, 5, 0, 7]});
          } catch (_) {
            formulasAsText++;
            result.push({text: node.querySelector('annotation[encoding="application/x-tex"]')?.textContent || node.textContent, font: "Mono", fontSize: 9, margin: [0, 4, 0, 6]});
          }
          return;
        }
        if (tag === "pre") {
          flush();
          // Separate lines allow long code blocks to paginate without clipping.
          for (const line of node.textContent.replace(/\t/g, "    ").split("\n")) {
            result.push({text: runs(line || " ", {font: "Mono"}), fontSize: 8.5, preserveLeadingSpaces: true,
              background: "#f3f5f8", margin: [8, 0, 0, 1]});
          }
          result.push({text: " ", fontSize: 4}); return;
        }
        if (tag === "ul" || tag === "ol") {
          flush();
          result.push({[tag]: [...node.children].map(li => ({stack: blocks(li)})), margin: [0, 3, 0, 5]}); return;
        }
        const heading = /^h[123]$/.test(tag) || node.classList.contains("note-heading");
        const block = heading || ["article", "p"].includes(tag) || node.classList.contains("note-para");
        if (block) flush();
        const next = {...style};
        if (heading || tag === "strong" || tag === "b") next.bold = true;
        if (tag === "em" || tag === "i") next.italics = true;
        if (tag === "code") { next.font = "Mono"; next.fontSize = 9; }
        if (tag === "a" && /^https?:\/\//i.test(node.getAttribute("href") || "")) { next.link = node.href; next.color = "#23547b"; }
        if (node.classList.contains("meta")) { next.fontSize = 8; next.color = "#526272"; }
        if (heading) next.fontSize = tag === "h1" ? 22 : tag === "h2" ? 14 : 10;
        if (heading) result.push({text: " ", fontSize: tag === "h2" ? 8 : 3});
        for (const child of node.childNodes) visit(child, next);
        if (block) flush();
      }
      for (const node of parent.childNodes) visit(node);
      flush(); return result;
    }
    return {document: {
      info: {title: "Practice notes", creator: "cosine"},
      pageSize: "A4", pageMargins: [42, 40, 42, 42],
      defaultStyle: {font: "Roboto", fontSize: 10, lineHeight: 1.25, color: "#18222c"},
      content: blocks(doc.body),
      footer: (page, pages) => ({text: `Practice notes  ·  ${page} / ${pages}`, alignment: "center", fontSize: 8, color: "#526272"}),
    }, formulasAsText};
  }
  async function create(html) {
    await load();
    const result = definition(html, mml => globalThis.MathJax.mathml2svg(mml).querySelector("svg"));
    const bytes = await globalThis.pdfMake.createPdf(result.document).getBuffer();
    return {bytes, formulasAsText: result.formulasAsText};
  }
  globalThis.cosineNotesPdf = {create, definition};
})();
