// One display vocabulary for result cards and exported Sheet cells.
(function (root) {
  const bands = ['Foundation', 'Standard', 'Intermediate', 'Advanced', 'Expert'];
  const tokens = bands.map(label => `cses-${label.toLowerCase()}`);
  const levels = ['high', 'medium', 'low'];
  // One place for the wording, because the card tooltip, the detail panel and
  // the manual all have to say the same thing about the same three words.
  const confidenceTitles = {
    high: 'high confidence: both independent solution reviews chose this band.',
    medium: 'medium confidence: the two reviews were one band apart; this is their rounded mean.',
    low: 'low confidence: the reviews were resolved by a specialist check rather than by agreement.',
  };
  // A band is only a band when it is CSES's own and inside the published range;
  // a foreign rating parked on a CSES record is not an estimate.
  function csesBand(problem) {
    if (!problem || problem.platform !== 'cses') return null;
    const meta = problem.cses_difficulty;
    if (!meta || typeof meta !== 'object') return null;
    return Number.isInteger(meta.band) && meta.band >= 1 && meta.band <= 5 ? meta : null;
  }
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
  // How much the two reviews agreed. Null for anything that isn't a published
  // CSES estimate, including a record written before confidence was stored.
  function confidence(problem) {
    const meta = csesBand(problem);
    return meta && levels.includes(meta.confidence) ? meta.confidence : null;
  }
  // Only what the record already carries — never the reviews themselves.
  function provenance(problem) {
    const meta = csesBand(problem);
    if (!meta) return null;
    return {
      band: meta.band,
      label: bands[meta.band - 1],
      confidence: confidence(problem),
      method: typeof meta.method === 'string' && meta.method ? meta.method : null,
      reviewedAt: typeof meta.reviewed_at === 'string' && meta.reviewed_at ? meta.reviewed_at : null,
      overridden: Boolean(meta.override),
    };
  }
  function confidenceTitle(level) {
    return confidenceTitles[level] || '';
  }
  root.cosineDifficulty = { bands, tokens, format, value, confidence, provenance, confidenceTitle };
  if (typeof module !== 'undefined' && module.exports) module.exports = root.cosineDifficulty;
})(typeof window === 'undefined' ? globalThis : window);
