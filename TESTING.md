# Testing — pickaxe

## Quick start

```bash
# All tests
pytest test_pickaxe.py -v

# By class
pytest test_pickaxe.py -v -k "Smoke"
pytest test_pickaxe.py -v -k "Diagnose"
pytest test_pickaxe.py -v -k "Discover"
pytest test_pickaxe.py -v -k "SessionLogging"
pytest test_pickaxe.py -v -k "CommitTrends"
```

No `pip install` required beyond `pytest`. All tests use stdlib + `subprocess` + the `git` binary on PATH. No network calls. No Azure/GitHub auth.

## Test matrix

| Class | Count | What it covers |
|---|---|---|
| `TestSmoke` | 12 | Module imports; `find_git_root`; `parse_header` (full + minimal + live file); `score_candidate`; `extraction_script`; CLI `--help` exit 0; `already_extracted` key present; same-repo not annotated (PX-B3) |
| `TestDiagnose` | 13 | `diagnose()` on healthy repo, detached folder, missing origin, stripped config; remote URL returned; never-mutates assertion; gitlink / submodule worktree (has_git, 'submodule' flag, origin resolution, missing_origin) |
| `TestDiscover` | 16 | `discover()` on empty dir, single repo, multiple repos; required keys; health_ok true/false; remote URL + branch returned; never-mutates assertion; live self-scan; gitlink submodule found + flagged + health_ok; `--submodules-only` excludes normal repos; `--submodules-only` empty when no submodules (PX-B1) |
| `TestSessionLogging` | 11 | `_save_session_event` creates NDJSON file; valid JSON per line; target is relative + forward-slash; multiple appends; `_build_discover_summary` flag counts; `_build_diagnose_summary` keys; CLI `discover --save` creates sessions dir; `_build_scan_summary` keys + empty-list edge case; CLI `scan --save` creates session entry |
| `TestCommitTrends` | 21 | `commit_trends()` exists + returns list + required keys; week/day/month format strings; count accuracy (3 commits same week → count=3); empty repo → `[]`; non-repo path → `[]`; chronological sort; `--from` / `--to` date filters; live pickaxe repo smoke; `render_trends_table` exists + prints PERIOD/COUNT headers + MARATHON flag + no false-positive at threshold; CLI exit 0; CLI `--format json` valid list with period+count; CLI `--by month` format; backward-compat `discover <path>` (no noun) |
| `TestBackupSmoke` | 10 | `backup()` manifest shape; bundle creation per repo; working-tree copy (no `.git`); `--skip-working-tree`; CLI exit 0; `--format json` |
| `TestRestoreSmoke` | 7 | `restore()` clone-from-bundle; origin remote re-added; `already_exists` / `missing_bundle` / `clone_failed` statuses; CLI exit 0 |
| `TestDiscoverDrift` | 8 | `discover drift` ahead/behind/dirty detection; `push-needed` / `behind` / `uncommitted` / `no-remote` / `fetch-failed` flags |
| `TestDiagnoseNounDispatch` | 3 | `diagnose instruction-bloat` noun routes correctly; backward-compat bare `diagnose <repo>` still works; unknown noun errors |
| `TestDiagnoseInstructionBloat` | 9 | 200-line file threshold detection; oversized-section detection; `--format json`; `--save` session event |
| `TestDeliverInstructionRollup` | 9 | `--from-report` plan generation (dry-run); `--execute` writes extracted files + pointer stub; missing `--from-report` errors |
| **Total** | **119** | |

## Fixture patterns

`repo_with_origin` / `repo_no_origin` / `repo_stripped_config` / `detached_folder` — `tmp_path` fixtures that write minimal fake `.git/` directories (no actual git commits, no network). Used by Diagnose and Discover tests for deterministic, fast assertions.

`_make_submodule_repo(parent, name, origin_url)` — helper that creates a submodule worktree (`.git` is a gitlink file pointing to `parent/.git/modules/<name>`). Mirrors what `git submodule add` produces.

`_make_git_repo_with_commits(tmp_path, name, commit_dates)` — creates a real git repo with one commit per supplied ISO date. Writes `.git/config` directly (skips global `~/.gitconfig` and `/etc/gitconfig`) to avoid `commit.gpgsign=true` failures on developer machines. Sets `GIT_CONFIG_NOSYSTEM=1` and `HOME=<tmp>` in the subprocess env for the same reason.

`script_full_header` / `script_minimal` — `tmp_path` fixtures that write `.py` files with complete vs bare headers for scoring tests.

## Known gaps / future tests

- `--execute` pipeline (Track A) — no tests yet; will require mocking `gh` CLI and
`git-filter-repo` or integration flag
- `pickaxe deliver drift` — not implemented; no tests
- `--holidays` annotation — tested only as a passthrough (no `holidays` package installed in
CI); correctness of period → holiday-name mapping is untested
- `--save` on `discover commit-trends` — the session event file is created but its content
is not asserted (shape test missing)
- Windows path separator in `_save_session_event` target field — asserted forward-slash in
`TestSessionLogging`; cross-platform replay not validated on macOS/Linux yet
- `render_trends_table` total/summary line is not asserted (only MARATHON flag and headers)

---

## Test run history

| Date | Runner | Python | Result | Duration | Notes |
|---|---|---|---|---|---|
| 2026-07-29 | pytest 9.0.3 | 3.14.5 (win32) | 119 passed / 0 failed | 181s | v0.4.0 — diagnose instruction-bloat + deliver instruction-rollup (A1-A4, first deliver verb); backup/restore/drift classes added since v0.3.4 |
| 2026-06-15 | pytest 9.0.3 | 3.14.5 (win32) | 73 passed / 0 failed | 141s | v0.3.4 — already_extracted (PX-B3) + --submodules-only (PX-B1) |
| 2026-06-14 | pytest 9.0.3 | 3.14.5 (win32) | 69 passed / 0 failed | 76s | v0.3.3 — commit-trends (21 new tests) |
| 2026-06-03 | pytest 9.0.3 | 3.14.5 (win32) | 48 passed / 0 failed | — | v0.3.2 — gitlink submodule support (diagnose + discover) |
| 2026-05-27 | pytest 9.0.3 | 3.14.5 (win32) | — | — | v0.3.0 — session logging, scan summary, `--save` flag |
