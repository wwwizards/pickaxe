# State: pickaxe

```
# --------------------------------------------------------------------------
# NOTES:    STATE.md
# --------------------------------------------------------------------------
# ABSTRACT: Live state of the pickaxe repo. Current version, open blockers,
#     active backlog. Updated at each session close.
# CREATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# UPDATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# VERSION:  0.2.0
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```

**Last updated:** 260612
**Current version:** v0.2.0 (commit `89a35c6`)

------------------------------

## Snapshot

- Phase: v0.2.0 — 5D command surface (discover + diagnose shipped)
- Status: active

## What shipped in v0.2.0

- `diagnose(path)` — reads `.git/config`, flags: `ok | missing_git | missing_origin | stripped_config`
- `discover(root)` — walks a tree for repo roots, emits `{path, rel, remote, branch, flags, health_ok}`
- `_get_branch(path)` — reads `.git/HEAD`, handles detached HEAD
- `test_pickaxe.py` — 30 tests (10 smoke baseline v0.1.1 + 9 diagnose + 11 discover), all green
- CLI: `pickaxe discover [root] [--format table|json]` and `pickaxe diagnose [path] [--format table|json]`
- Legacy positional scan preserved for backward compat

## Current focus

Track B — repo hygiene and drift control. Next: manifest-driven deliver.

## Next actions

1. Define `repos.manifest.json` schema (path, expected_remote, branch, hygiene_baseline)
2. `pickaxe deliver dirs` — clone missing repos / restore missing remotes from manifest
3. `pickaxe discover drift` — diff local inventory vs manifest, report mismatches
4. Session log schema design (D-07) — must precede execution pipeline (PX-01)

## Risks / blockers

- `discover` does not yet skip nested repos inside an already-found repo (may need `--no-recurse`)
- No `repos.manifest.json` schema yet — blocks `deliver` and `drift`

------------------------------

## Backlog

| ID | Task | Status | Notes |
|---|---|---|---|
| PX-01 | v0.2 execution pipeline (`--execute`, subdir mode, `.pickaxe/` chain-of-custody) | Design complete — not started | Requires D-07 session log schema first |
| PX-02 | Session log schema design (D-07) | Not started | Must precede PX-01; feeds AIM training data pattern |
| PX-03 | `repos.manifest.json` schema + `deliver dirs` + `discover drift` | In design | See Next actions above |
| PX-04 | v0.3 cluster detection | Not started | Waiting on PX-01 |
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
  and `.git`-as-file (submodule worktree gitlink, format: `gitdir: <relative-path>`).
  All git-touching code goes through this single resolver.
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

Track C (Submodule Hygiene) — consistent submodule workflow for LogicWizards mono-repo
so each subproject can have its own remote & upstream.

## Next 3 actions

1. **Address orphaned repos** — `clipd` and `redact` have `.git` dirs but are NOT in
   `.gitmodules`. Options: (a) register as submodules, (b) give own remotes and document
   as "sibling repos, not submodules". Design decision needed before implementing.
2. **Submodule hygiene template** — pre-commit hook (clean working tree in submodule),
   pre-push hook (verify submodule commits exist on remote). Use `.githooks/` committed
   to the monorepo (Option B). This feeds `pickaxe design` + `pickaxe deliver` phases.
3. **ROADMAP Track C entry** — gitlink support + submodule workflow template warrants its
   own track. User noted: "it pro'ly warrants at least one MVx & should feed a case study."

## Risks / blockers

- `clipd` and `redact` are orphaned (have `.git` dirs, no `.gitmodules` entry, no
  `wwwizards` GitHub remote confirmed). Resolution needed before hook template can be
  applied uniformly to all 7 repos in SIDE-PROJECTS.
- No `.githooks/` template exists yet — blocks enforcement of submodule hygiene policy.

## Handoff note

48/48 pytest green. Run `python -m pytest test_pickaxe.py -v` to validate.
Run `python pickaxe.py discover SOLUTIONS/DevOps/SIDE-PROJECTS --format table` to see
all 7 repos including ipscan with `submodule` flag.
See `.HANDOFF/DESIGN.md` for full 5D command surface. pytest required (`python -m pip install pytest`).
