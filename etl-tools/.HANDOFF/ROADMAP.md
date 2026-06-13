# etl-tools — ROADMAP.md

CREATED: 2026-06-01
MODULE: etl-tools (part of pickaxe monorepo)

---

## v0.4.x — Maintenance (CURRENT)

**Shipped:** v0.4.2 (2026-06-01)

- [x] stdin support (`-f -`)
- [x] `--columns` / `-c` flag with display-order control
- [x] List-cell flattening (`_cell()`)
- [x] Cross-platform CSV line endings (`sys.stdout.reconfigure`)

---

## v0.5.0 — Query Enhancements (PLANNED)

**Goal:** Numeric comparison and sort control.

- [ ] Numeric operators: `>`, `<`, `>=`, `<=` (auto-detect field type)
- [ ] `--sort FIELD` flag (ascending by default, `--sort-desc` for reverse)
- [ ] `--limit N` flag (top-N rows after filter+sort)
- [ ] Tests: `test_convert_from_json.py` — cover filter engine edge cases,
      column selection, sort, limit, stdin mock

**Trigger:** When querying probe data with thresholds, e.g.
`-q "gpu0_util_pct > 50"` to filter only active-GPU snapshots.

---

## v0.6.0 — Output Enhancements (PLANNED)

**Goal:** Additional output targets.

- [ ] `--output markdown` — GitHub-flavored markdown table (pipe-friendly for docs)
- [ ] `--output tsv` — tab-separated (Excel-paste friendly)
- [ ] `--no-header` flag for CSV/TSV (append-friendly pipelines)
- [ ] `--output html` — minimal table (for dashboard embedding)

**Trigger:** When MVx case study tables need to go directly into markdown reports
without manual reformatting.

---

## v0.7.0 — Diff Mode (PLANNED)

**Goal:** Native before/after comparison without needing sys-diff.py.

```
python convert_from_json.py -f probes.json --diff --before baseline --after post-tier1
                            -c "field,before,after,delta,change_pct"
```

**Scope:**
- [ ] `--diff` flag with `--before LABEL` and `--after LABEL`
- [ ] Auto-compute delta (numeric fields only) and change_pct
- [ ] Highlight rows exceeding a threshold (`--highlight-threshold N`)

**Note:** This overlaps with `sys-diff.py` in sys-tools roadmap. Decision point:
if diff logic is purely presentation (format two records as a diff table), it
belongs here. If it's domain-specific (GPU probe comparison), it belongs in
sys-tools. Defer until v0.5.0 is shipped and real use case is clearer.

---

## Backlog (No Version Assigned)

- Packaging: `pyproject.toml` so `from pickaxe.etl_tools import from_json` works
  cleanly from other pickaxe sub-modules without sys.path hacks.
- `from_json()` module API: add `data=` parameter for in-memory input (bypasses
  file open, enables use as a pure formatter in other scripts).
- Encoding: `--encoding` flag to handle non-UTF-8 input files.
- Large file streaming: current impl loads full JSON into memory. For files
  >100MB, consider `ijson` (streaming JSON parser) — out of scope until needed.
