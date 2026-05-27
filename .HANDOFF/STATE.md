# STATE.md

## Snapshot

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
