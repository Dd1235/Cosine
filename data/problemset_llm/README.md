# problemset_llm

Generated problem records from `Problems/urls.txt`.

Use:

```sh
OPENAI_API_KEY=... python3 scripts/annotate_problem_urls.py --limit 20
```

Trial run:

```sh
python3 scripts/annotate_problem_urls.py \
  --sample-one-per-platform \
  --out data/problemset_llm_trial \
  --overwrite \
  --insecure-ssl
```

The URL list is the source of truth for `source_url` and `source_topic`.
The LLM should only produce the normalized `statement`, `tags`, and `patterns`.

The script loads root `.env` and accepts either `OPENAI_API_KEY` or `OPEN_AI_API`.

Platform-specific runs:

```sh
python3 scripts/annotate_problem_urls.py --platform leetcode --out data/problemset_llm --insecure-ssl
python3 scripts/annotate_problem_urls.py --platform cses --out data/problemset_llm --insecure-ssl
python3 scripts/annotate_problem_urls.py --platform codeforces --out data/problemset_llm --insecure-ssl
```

On macOS, keep the machine awake during long runs:

```sh
caffeinate -dimsu python3 scripts/annotate_problem_urls.py --platform leetcode --out data/problemset_llm --insecure-ssl
```

Codeforces pages are often Cloudflare-blocked. The script skips entries without
usable statement text unless `--allow-metadata-only` is passed.

## External judges: `kattis/`, `codechef/`, Codeforces Gym

These directories are **not** produced by `annotate_problem_urls.py`. Their
records come through a reviewed pipeline:

1. `python3 scripts/ingest_contest.py <kattis problem-source or contest URL>`
   stages statements into `data/analysis/external-staging/<id>.json`
   (`source_text`, `source_url`, and for Kattis `kattis_difficulty`
   `{score, label, host, observed_at}` plus `contest_source`). CodeChef
   problems stage through `scripts/external_judges.py`.
2. An agent derives the solution and proposes labels →
   `data/analysis/external-proposals.json` (`batch` per proposal).
3. An independent skeptic reviews → `data/analysis/external-review.json`, each
   entry pinned to `source_text_sha256`.
4. `python3 scripts/publish_external.py --batch <name> --write` writes the
   record here, then `npm run embed && npm run validate`.

Fields specific to these records: `kattis_difficulty` (per-host Kattis score,
metadata only — never a rating, never filtered or sorted on), `difficulty:
null`, and `annotation.evidence` pointing at the review file. CSES records
carry `cses_difficulty` (`band` 1–5, `confidence`, `method`, `evidence`,
`statement_sha256`) — see `data/cses/README.md`.

