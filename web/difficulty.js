// One display vocabulary for result cards and exported Sheet cells.
(function (root) {
  const bands = ['Foundation', 'Standard', 'Intermediate', 'Advanced', 'Expert'];
  const tokens = bands.map(label => `cses-${label.toLowerCase()}`);
  function format(problem) {
    if (problem.platform === 'cses') {
      const band = problem.cses_difficulty && problem.cses_difficulty.band;
      return Number.isInteger(band) && band >= 1 && band <= 5 ? `${bands[band - 1]} · CSES estimate` : '';
    }
    return problem.difficulty == null ? '' : String(problem.difficulty);
  }
  function value(problem) {
    if (problem.platform === 'cses') {
      const band = problem.cses_difficulty && problem.cses_difficulty.band;
      return Number.isInteger(band) && band >= 1 && band <= 5 ? band : null;
    }
    const d = problem.difficulty;
    if (typeof d === 'number' && Number.isFinite(d)) return d;
    return ({ Easy: 1, Medium: 2, Hard: 3 })[d] || null;
  }
  root.cosineDifficulty = { bands, tokens, format, value };
  if (typeof module !== 'undefined' && module.exports) module.exports = root.cosineDifficulty;
})(typeof window === 'undefined' ? globalThis : window);
