# etl-tools — STATE.md

UPDATED: 2026-06-01
MODULE: etl-tools (part of pickaxe monorepo)

---

## Current Version: v0.4.2

### What shipped

| Version | Date | Change |
|---|---|---|
| v0.3.1 | 2024-10-05 | Module-ready (`__init__.py`, importable as `converters` package) |
| v0.4.0 | 2026-05-27 | stdin support (`-f -`), `--columns` flag, list-cell flattening |
| v0.4.1 | 2026-06-01 | Cross-platform CSV line endings (io.TextIOWrapper approach) |
| v0.4.2 | 2026-06-01 | Simplified to `sys.stdout.reconfigure(newline='\n')` — cleaner, no extra import |

### Status: stable

All three output formats (table/csv/json) working. Stdin pipe validated
end-to-end with `sys-probe.py`:

```powershell
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "baseline" --no-intel `
  | .venv\Scripts\python.exe etl-tools\convert_from_json.py -f - -o table `
  -c "timestamp,label,cpu_util_pct,gpu0_util_pct,gpu0_vram_used_mb,gpu0_temp_c,gpu0_pstate"
```

Filter engine working: `=`, `!=`, glob (`*`), `and`, `or`.

---

## Open Items

- [ ] Numeric comparison operators (`>`, `<`, `>=`, `<=`) — currently string-only
- [ ] `--sort FIELD` flag for output ordering
- [ ] Intel GPU WMI fields render fine when present; no special handling needed
- [ ] `from_json()` module API: `file_path` only, no stdin support when imported
      (minor gap — not blocking any current use case)

---

## Python Environment

Requires: Python 3.7+ (for `reconfigure()`), pure stdlib — no pip installs needed.
Works in `.venv` and system Python alike (no third-party deps).

---

## Key Files

| File | Purpose |
|---|---|
| `convert_from_json.py` | Main tool — ingestion, filter, format |
| `__init__.py` | Package init — exposes `from_json` when imported as module |
| `README.md` | Human-readable setup and usage guide |
| `.HANDOFF/DESIGN.md` | Architecture, pipe contract, module API |
| `.HANDOFF/STATE.md` | This file |
| `.HANDOFF/ROADMAP.md` | Planned enhancements |
