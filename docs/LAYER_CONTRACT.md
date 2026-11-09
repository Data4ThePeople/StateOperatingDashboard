# Layer contract (how fetch scripts hand data to the dashboard)

Project: Ohio county operating dashboard. 88 counties, FIPS 39001..39175 (odd numbers).
Python: `.venv/bin/python` (Python 3.9: no `match`, no `X | Y` type hints). pandas and requests installed.
Shared helpers: `scripts/common.py` (`get`, `cached`, `bls_series`, `census`, `write_json`, `RAW`, `PROC`, `STATE="39"`).
Keys come from `get_key("BLS_API_KEY")`, `get_key("CENSUS_API_KEY")`; never print or copy them.
Raw downloads go under `data/raw/<source>/` (cached; re-runs read the cache).

Each layer script writes one file `data/processed/<layer>.json`:

```json
{
  "metrics": {
    "<metric_id>": {
      "label": "Unemployment rate",            // plain words, 8th-grade
      "theme": "jobs | income | health | people",
      "unit": "pct | usd | count | per100k | years | index",
      "decimals": 1,
      "better": "higher | lower | none",        // direction that is good for residents; "none" if not a judgment
      "source": "BLS Local Area Unemployment Statistics",
      "vintage": "annual averages 2000-2025; pulled 2026-11-09",
      "period_label": "2025 annual average",    // what the latest value refers to
      "note": "one or two plain sentences: what it counts and the main caveat"
    }
  },
  "counties": {
    "39001": {
      "<metric_id>": {"latest": 5.1, "period": "2025", "series": [["2015", 6.2], ["2016", 5.9]], "moe": null, "flag": null}
    }
  },
  "ohio": { "<metric_id>": {"latest": ..., "period": ..., "series": [...]} },
  "extras": { "<name>": { "39001": <any JSON>, "ohio": <any JSON> } }
}
```

Rules
- Every one of the 88 counties appears in `counties`. A missing or suppressed value is `null` with `"flag": "suppressed"` (or another short reason), never 0.
- `series` is chronological; periods are strings ("2025", "2025-09", "2020-2024"). No duplicate periods (fail hard if found).
- Store values at full precision; the page rounds once.
- Shares are percentages 0-100, not 0-1.
- Ohio statewide values come from the publisher's own state figure, not a sum or average of counties, unless no state figure exists (then say so in `note`).
- Write `docs/datasets/<layer>.md` with one DATASETS.md section per source (template: ~/.claude/d4tp-process/templates/DATASETS.md). Read the publisher's method docs, not just the product page. Keep it factual and short; American spelling; no em dashes.
- Do not commit, do not edit files you did not create, do not touch `dist/`.
