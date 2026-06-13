# sys-tools — ROADMAP.md

CREATED: 2026-06-01
MODULE: sys-tools (part of pickaxe monorepo)

---

## v0.1.0 — sys-probe (CURRENT)

**Shipped:** 2026-06-01

- [x] `sys-probe.py` — point-in-time JSON snapshot (CPU, RAM, NVIDIA GPU, Intel GPU)
- [x] `--label` flag for MVx experiment tagging
- [x] `--interval` / `--count` for monitor loop mode
- [x] `--output FILE` for probe accumulation (append to JSON array)
- [x] `--no-intel` flag to skip slow WMI query
- [x] Pipe contract: stdout JSON → `convert_from_json.py -f - -o table`
- [x] `.HANDOFF/` structure: DESIGN.md, STATE.md, ROADMAP.md

---

## v0.2.0 — sys-diff (PLANNED)

**Goal:** Structured before/after comparison from a labeled probes file.

```
python sys-diff.py --file probes.json --before baseline --after post-tier1
                   [--format table|json|csv]
```

Output: diff table with `field | before | after | delta | change_pct`

**Scope:**
- [ ] `sys-diff.py` — reads two labeled records from a probes file, emits diff
- [ ] Auto-align numeric fields (delta + %) vs string fields (changed/unchanged)
- [ ] `--highlight` flag — mark rows where delta exceeds a threshold
- [ ] Tests: `test_sys_diff.py` with fixture probes files

**Trigger:** After post-Tier-1 and post-Tier-2 probes are captured and the MVx
case study needs a clean structured comparison rather than manually reading tables.

---

## v0.3.0 — sys-watch (PLANNED)

**Goal:** Live terminal dashboard for real-time GPU/CPU monitoring during benchmarks.

```
python sys-watch.py [--interval N] [--output FILE] [--no-intel]
                    [--columns col1,col2,...]
```

Output: rich-based in-place updating terminal panel (uses `rich.live`).
Simultaneously appends to `--output FILE` if specified.

**Scope:**
- [ ] `sys-watch.py` — live panel using `rich.Live` + `rich.Table`
- [ ] Configurable refresh interval (default 2s)
- [ ] Simultaneous file append (same format as sys-probe --output)
- [ ] Graceful Ctrl-C exit with final summary line
- [ ] Tests: `test_sys_watch.py` (mock psutil/nvidia-smi for unit coverage)

**Dependencies:** `rich` (already installed in .venv)

**Trigger:** When doing CuPy benchmarks or GPU stress tests and wanting to watch
GPU-0 utilization climb in real time rather than running discrete probes.

---

## v0.5.0 — git-health (FUTURE — born from FAIL #26)

**Goal:** Detect and fix git repo hygiene issues in a workspace — specifically the
unregistered-gitlink anti-pattern that bites every new clone and CI run.

```
python git-health.py <repo-root> [--fix] [--output report.md]
```

**Core check — unregistered gitlinks:**
- Walk `git ls-files --stage` output looking for mode `160000` entries
- For each, check whether a matching `[submodule]` block exists in `.gitmodules`
- Report mismatches as `UNREGISTERED` findings with the inferred remote URL
  (reads from `.git/config` or the nested repo's `git remote -v`)
- `--fix`: runs `git config --file .gitmodules ...` + `git config --local ...` for each
  finding and stages `.gitmodules`

**Additional checks (stretch):**
- Submodule pointer drift: HEAD in parent != HEAD in nested repo
- Nested `.git` folders that are NOT tracked as gitlinks at all (forgotten repos)
- `.gitmodules` entries with no corresponding path on disk (stale/removed submodules)

**Origin:** FAIL #26 in `.HANDOFF/LIGHTBULB-LOG.md` — 3 repos (ai-labs, psst, psstel)
were tracked as gitlinks for months with no `.gitmodules` entry. Every `git submodule
status` threw a fatal. Fixed manually in ~30 min on 2026-06-01; should have been a
one-command tool.

**Scope:**
- [ ] `git-health.py` — scan + report unregistered gitlinks
- [ ] `--fix` mode — auto-register with inferred URL, stage `.gitmodules`
- [ ] Tests: fixture repo with known gitlink states
- [ ] README entry (git-tools section)

---

## v0.4.0 — sys-report (FUTURE)

**Goal:** Generate a markdown summary of a probes session with embedded tables.

```
python sys-report.py --file probes.json --output report.md [--filter label=post-*]
```

Output: Markdown file with sections per label, formatted tables, and auto-computed
diffs between first and last records in the session.

**Trigger:** When capturing a long monitoring session and wanting a shareable
snapshot document rather than a raw JSON file.

---

## Backlog (No Version Assigned)

- Intel GPU WMI query: validate and harden the PowerShell fallback on this machine.
  Currently `--no-intel` is default for speed; should eventually work reliably.
- `--format` flag on sys-probe.py to support inline table output without piping to
  convert_from_json (requires bundling the table renderer or importing from etl-tools
  via a well-defined import path).
- Packaging: consider making sys-tools a proper Python package (`__init__.py`,
  `pyproject.toml`) so `from sys_tools import probe` works in other pickaxe modules.
- Cross-platform: probe_nvidia() is NVIDIA-only; probe_intel_gpu() is Windows-only.
  Add `sys.platform` guards and stubs for Linux/macOS portability.
- **macOS / Apple Silicon GPU probe:** `powermetrics --samplers gpu_power` exposes
  GPU active residency, freq, and power on M-series chips. Would need `sudo` or a
  launchd helper — good candidate for a `probe_apple_gpu()` function behind a
  `--no-apple` flag (mirrors `--no-intel` pattern). Investigate: do Apple Silicon
  probes need a separate `sys-probe-mac.py` or can they live in the same file behind
  `sys.platform == 'darwin'` guards? Test machine: MacBook (architecture TBD).
  **Trigger:** When macOS machine is available for hands-on testing.
