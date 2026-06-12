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
- Date: 2026-05-26
- Phase: v0.2.0 — 5D command surface (discover + diagnose shipped)
- Status: active

## What shipped in this session

- `diagnose(path)` — reads `.git/config`, flags: `ok | missing_git | missing_origin | stripped_config`
- `discover(root)` — walks a tree for repo roots, emits `{path, rel, remote, branch, flags, health_ok}`
- `_get_branch(path)` — reads `.git/HEAD`, handles detached HEAD
- `test_pickaxe.py` — 30 tests (10 smoke baseline v0.1.1 + 9 diagnose + 11 discover), all green
- CLI: `pickaxe discover [root] [--format table|json]` and `pickaxe diagnose [path] [--format table|json]`
- Legacy positional scan (`python pickaxe.py [root]`) preserved for backward compat
- DESIGN.md: 5D command surface documented, prior names (doctor/inventory) cross-referenced
- ROADMAP Track B: updated to use 5D command names

## Current focus

Track B — repo hygiene and drift control. Next: manifest-driven deliver.

## Next 3 actions

1. Define `repos.manifest.json` schema (path, expected_remote, branch, hygiene_baseline)
2. `pickaxe deliver dirs` — clone missing repos / restore missing remotes from manifest
3. `pickaxe discover drift` — diff local inventory vs manifest, report mismatches

## Risks / blockers

- `discover` does not yet skip nested repos inside an already-found repo (LogicWizards + pickaxe both found when scanning from LogicWizards root — currently correct behaviour, but may need a `--no-recurse` flag)
- No `repos.manifest.json` schema yet — blocks `deliver` and `drift`

## Handoff note

See `.HANDOFF/DESIGN.md` for full 5D command surface. Run `python -m pytest test_pickaxe.py -v` to validate. pytest must be installed (`python -m pip install pytest`).