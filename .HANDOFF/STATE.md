# State: pickaxe

```
# --------------------------------------------------------------------------
# NOTES:    STATE.md
# --------------------------------------------------------------------------
# ABSTRACT: Live state of the pickaxe repository, including shipped commands,
#           active design contracts, blockers, and next implementation work.
# CREATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# UPDATED:  260730 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON
# ARCHITECT: JN (Joe Negron -- LogicWizards.NYC)
# TECHLEAD:  JN (Joe Negron -- LogicWizards.NYC)
# VERSION:  0.4.2
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```


------------------------------

## Snapshot

- Shipped CLI is now v0.4.2 (260729) — `diagnose instruction-bloat` (A1/A3) + `deliver instruction-rollup` (A2/A4, first-ever `deliver` verb), plus two follow-on bugfixes: LB-03 (data loss on overlapping findings) and LB-04 (`.github/` sources now route to `.github/instructions/` for VS Code auto-discovery). 123/123 tests green. Dogfood-validated 260730 by running `diagnose instruction-bloat` against the root repo's live `.github/copilot-instructions.md` (correctly flagged all 6 oversized sections a manual review had independently found) — see [`pickaxe/ROADMAP.md`](../ROADMAP.md) "Dogfood validation" section and root-repo memory `/memories/repo/instructions-bloat-backlog.md`. See [SESSIONS/260729-Reconciliation-Handoff-forQ3Features/SESSION.md](SESSIONS/260729-Reconciliation-Handoff-forQ3Features/SESSION.md) for the original v0.4.0 session.
- [AI Training Manifest Contract](AI-TRAINING-MANIFEST.md) v0.1.0 is the canonical design for nearest-owner routing, active-context resolution, evidence isolation, and governed promotion.
- Pickaxe is the sole Federation resolver, classifier, synchronizer, and promoter. ai-labs owns protocol and promotion targets; ai-labs-toolkit may consume output but does not duplicate traversal or classification.
- The contract is design-only. `pickaxe context discover|route|resolve|check|promote` are not implemented yet.
- Parent-monorepo pointer updates are intentionally deferred because other sessions have staged parent work.

## Next actions

1. Inventory current root `.AI-TRAINING/` artifacts without moving files.
2. Implement the read-only `pickaxe context discover <path>` slice with focused tests.
3. Implement `pickaxe context route <artifact>` using deepest-applicable-owner resolution.
4. Present the generated routing plan for human approval before any `git mv` or promotion.
5. `handoff-rollup` POC in progress against `.sandbox/rollup-poc-260729/STATE.md` (gitignored copy, not this live file) — design + phased plan: [260728-Root-STATE-Rollup-Automation-Discovery](../../../../../.AI-TRAINING/mvx-stories/260728-Root-STATE-Rollup-Automation-Discovery.md). Not Federation-gated (Track B); unblocked now.

## Current blockers

- No implementation blocker for the first read-only slice.
- Parent pointer update and parent handoff are deferred to the coordinating monorepo session.
- Federation implementation remains pinned until the Wizard explicitly names the first MVx.

------------------------------

## Shipped baseline

## What shipped in v0.4.1/v0.4.2 (260729)

- LB-03 fix: `deliver instruction-rollup` was silently dropping every extraction after
the first when a whole-file finding overlapped section findings (mutation-order bug,
read-after-truncate). Fixed via snapshot-before-mutate + `skipped_overlap` status.
Caught via sandbox test, never touched a live file.
- LB-04 fix: `.github/` sources were extracting to `.github/` directly, a location VS
Code's Copilot instructions auto-discovery never scans (`.github/instructions/*.instructions.md`
is the actual convention). Fixed via a `.github`-aware dest router + source-dir-relative
pointer links. Found via code review before any live `--execute` run.
- `test_pickaxe.py` — 123 tests total (4 new regression tests across both fixes), all green.
- Dogfood-validated 260730 against the root monorepo's own `.github/copilot-instructions.md`
via `diagnose instruction-bloat` (read-only, no `--execute`) — confirms detection is
production-correct; a controlled `--execute` dry-run comparison is the next step before
trusting a live rollup again on that file.

## What shipped in v0.4.0 (260729)

- `diagnose instruction-bloat` (A1/A3) — noun-dispatch retrofit onto `diagnose`; flags
instruction/handoff/memory files over the 200-line reliability threshold, plus oversized sections within them (`--format json`, `--save`)
- `deliver instruction-rollup` (A2/A4) — first-ever `deliver` verb shipped to production;
consumes a `diagnose instruction-bloat --format json` report via `--from-report`, plans extraction of oversized sections into scoped child files + pointer stub (dry-run by default, `--execute` to write)
- `test_pickaxe.py` — 119 tests total (21 new: `TestDiagnoseNounDispatch` 3,
`TestDiagnoseInstructionBloat` 9, `TestDeliverInstructionRollup` 9), all green
- README.md, TESTING.md — synced with instruction-bloat/instruction-rollup usage + test
matrix (260729, post-hoc during reconciliation session)
- Committed `d9b3aa2` on `main`, pushed to `wwwizards/pickaxe`

## What shipped in v0.3.4 (260615)

- `scan()` — `already_extracted` field on every candidate; non-null when file lives in a
different git root than the scan root (annotates `[extracted → <remote>]` in table + JSON)
- `_get_remote_url(path)` helper — returns origin URL for any git repo path
- `render_table()` — NOTE column added; shows `already_extracted` annotation
- `_cmd_scan` JSON output — `already_extracted` field included
- `discover --submodules-only` flag — filters repo map to gitlink (submodule) entries only
- `test_pickaxe.py` — 73 tests total (4 new: 2 PX-B3 in TestSmoke, 2 PX-B1 in TestDiscover), all green
- ROADMAP.md — `--format json` marked ✅ shipped; Track B PX-B1 + PX-B3 checked off

## What shipped in v0.3.3

- `commit_trends(repo_path, by, from_date, to_date)` — weekly/daily/monthly cadence from `git log`; returns `[{period, count}]`
- `render_trends_table(trends, by, marathon_threshold, locale)` — PERIOD/COUNT/FLAG/NOTES table; MARATHON flag for periods exceeding threshold
- `_load_holidays(locale, by, trends)` — optional `holidays` package integration for period annotation
- `_cmd_discover_commit_trends(args)` — CLI handler dispatched from `discover` noun
- `discover` subparser extended with noun dispatch (`commit-trends` | `drift`); all prior flags preserved
- `test_pickaxe.py` — 69 tests total (21 new in `TestCommitTrends`), all green
- README.md — usage examples for discover/diagnose/commit-trends; prerequisites updated; roadmap checklist
- ROADMAP.md — `diagnose`, `discover`, `discover commit-trends` checked off in Track B
- TESTING.md — created; full test matrix, fixture patterns, known gaps, run history

## What shipped in v0.3.2 (260603)

- `_resolve_git_dir(path)` — resolves gitlink files (submodule worktrees)
- `diagnose` + `discover` updated to handle `.git` as file (submodule)
- 14 diagnose tests + 13 discover tests, gitlink coverage

## What shipped in v0.2.0 (260612)

- `diagnose(path)` — flags: `ok | missing_git | missing_origin | stripped_config`
- `discover(root)` — repo map with `{path, rel, remote, branch, flags, health_ok}`
- 30 tests (10 smoke + 9 diagnose + 11 discover)

## Next actions

1. Define `repos.manifest.json` schema (path, expected_remote, branch, hygiene_baseline)
2. `pickaxe deliver dirs` — clone missing repos / restore missing remotes from manifest
3. `pickaxe discover drift` — diff local inventory vs manifest, report mismatches
4. Session log schema design (D-07) — must precede execution pipeline (PX-01)

## Risks / blockers

- `discover` does not yet skip nested repos inside an already-found repo (may need `--no-recurse`)
- No `repos.manifest.json` schema yet — blocks `deliver` and `drift`
- `--holidays` annotation untested end-to-end (no `holidays` package in CI)

------------------------------

## Current focus

Track B continued — `discover drift` + `deliver dirs` (manifest-driven). Track D MQL design in progress.

## Next actions

1. Define `repos.manifest.json` schema (path, expected_remote, branch, hygiene_baseline)
2. `pickaxe discover drift` — diff local inventory vs manifest, report mismatches
3. `pickaxe deliver dirs` — clone missing repos / restore missing remotes from manifest
4. Session log schema design (D-07) — must precede execution pipeline (PX-01)

------------------------------

## Backlog

| ID | Task | Status | Notes |
|---|---|---|---|
| PX-01 | v0.2 execution pipeline (`--execute`, subdir mode, `.pickaxe/` chain-of-custody) | Design complete — not started | Requires D-07 session log schema first |
| PX-02 | Session log schema design (D-07) | Not started | Must precede PX-01; feeds AIM training data pattern |
| PX-03 | `repos.manifest.json` schema + `deliver dirs` + `discover drift` | In design | Next Track B milestone |
| PX-04 | v0.3 cluster detection | Not started | Waiting on PX-01 |
| PX-05 | `--holidays` end-to-end test | Not started | Needs `holidays` pkg in CI |
| PX-05 | v0.4 workspace init/split commands | Design complete — not started | `pickaxe init`, `pickaxe workspace init`, `pickaxe workspace split` |
| PX-06 | `--format json` output | Not started | v0.5 scope |
| PX-07 | GitHub Actions workflow | Not started | v0.5 scope |

------------------------------

## Completed

| Item | Date | Notes |
|---|---|---|
| v0.1.0 init — liberated from wwwizards mono-repo | 260506 | `a6149f3` |
| README + header polish, AUTODOC footer | 260518 | `711dae5` |
| `.pickaxe/` schema, AI context detection, `--install-deps` docs | 260518 | `8318f86` |
| `--dry-run` pipeline output v0.1.1 | 260519 | `a0e22b6` |
| 5D command surface (discover + diagnose) v0.2.0 | 260526 | `89a35c6` |
| `.HANDOFF/` bootstrapped; v0.4 workspace design captured | 260612 | This session |


- Project: pickaxe
- Date: 2026-06-03
- Phase: v0.3.2 — gitlink submodule support
- Status: active

## What shipped in this session (v0.3.2)

### Gitlink blind-spot fix (root cause: `os.path.isdir('.git')` fails for submodule worktrees)

- `_resolve_git_dir(path)` — new canonical helper; handles both `.git`-as-dir (normal repo)
and `.git`-as-file (submodule worktree gitlink, format: `gitdir: <relative-path>`). All git-touching code goes through this single resolver.
- `find_git_root()` — updated to accept gitlink files
- `_get_branch()` — uses `_resolve_git_dir` for HEAD resolution
- `diagnose()` — reads config from resolved gitdir; new `submodule` flag when gitlink detected
- `discover()` — accepts `isfile` for `.git` marker in addition to `isdir`
- `health_ok` logic changed: `flags == ['ok']` → `health['has_git'] and health['has_origin']`
so submodules with valid origin are correctly reported as healthy (not WARN)
- `test_pickaxe.py` — 7 new gitlink tests (4 diagnose + 3 discover); `_make_submodule_repo()`
helper fixture added; `repo_with_origin` fixture restored. **48/48 passed.**

### Verified in production
- `pickaxe discover SIDE-PROJECTS --format table` — ipscan now appears with `submodule` flag
(was silently missing before v0.3.2 due to gitlink blind-spot)

## What was learned (R&D input for pickaxe roadmap)

- Git submodule worktrees have `.git` as a **file**, not a directory. Content: `gitdir: <rel-path>`
pointing into `.git/modules/<name>/` in the parent repo's store.
- `os.path.isdir('.git')` is the wrong primitive for "is this a git repo". Use `_resolve_git_dir`.
- The correct test for "is this a submodule worktree" is: `.git` exists AND is a file AND
starts with `gitdir:`.
- Submodules in LogicWizards monorepo (registered in `.gitmodules`): `ipscan`, `ai-labs`,
`pickaxe`, `psst`, `psstel`.
- Orphaned loose repos (have `.git` dirs but NOT in `.gitmodules`): `clipd`, `redact`.
These need to either be registered as submodules or given their own proper remotes.

## Previous session (v0.2.0 → v0.3.1)

- `diagnose(path)` — reads `.git/config`, flags: `ok | missing_git | missing_origin | stripped_config`
- `discover(root)` — walks a tree for repo roots, emits `{path, rel, remote, branch, flags, health_ok}`
- `_get_branch(path)` — reads `.git/HEAD`, handles detached HEAD
- CLI: `pickaxe discover [root] [--format table|json]` and `pickaxe diagnose [path] [--format table|json]`
- Legacy positional scan (`python pickaxe.py [root]`) preserved for backward compat
- Session logging: `save_session_event`, `build_discover_summary`, `build_diagnose_summary`

## Current focus

Track C (Submodule Hygiene) — consistent submodule workflow for LogicWizards mono-repo so each subproject can have its own remote & upstream.

## Next 3 actions

1. **Address orphaned repos** — `clipd` and `redact` have `.git` dirs but are NOT in
`.gitmodules`. Options: (a) register as submodules, (b) give own remotes and document as "sibling repos, not submodules". Design decision needed before implementing.
2. **Submodule hygiene template** — pre-commit hook (clean working tree in submodule),
pre-push hook (verify submodule commits exist on remote). Use `.githooks/` committed to the monorepo (Option B). This feeds `pickaxe design` + `pickaxe deliver` phases.
3. **ROADMAP Track C entry** — gitlink support + submodule workflow template warrants its
own track. User noted: "it pro'ly warrants at least one MVx & should feed a case study."

## Risks / blockers

- `clipd` and `redact` are orphaned (have `.git` dirs, no `.gitmodules` entry, no
`wwwizards` GitHub remote confirmed). Resolution needed before hook template can be applied uniformly to all 7 repos in SIDE-PROJECTS.
- No `.githooks/` template exists yet — blocks enforcement of submodule hygiene policy.

## Handoff note

48/48 pytest green. Run `python -m pytest test_pickaxe.py -v` to validate. Run `python pickaxe.py discover SOLUTIONS/DevOps/SIDE-PROJECTS --format table` to see all 7 repos including ipscan with `submodule` flag. See `.HANDOFF/DESIGN.md` for full 5D command surface. pytest required (`python -m pip install pytest`).
