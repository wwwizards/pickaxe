# LIGHTBULB-LOG.md — pickaxe

Lessons learned during pickaxe R&D. Each entry = a real discovery from a real
session. These feed the roadmap, case studies, and any future video/whitepaper.

---

## LB-01 — Git submodule worktrees are invisible to `os.path.isdir('.git')`

**Date:** 2026-06-03  
**Version:** v0.3.1 → v0.3.2  
**Category:** git internals / discovery blind-spot

### What happened

`pickaxe discover SIDE-PROJECTS` returned 6 repos. `ipscan` — a registered
submodule with its own GitHub remote — was silently absent. No error, no
warning, just a missing row.

`pickaxe diagnose ipscan` falsely reported `has_git: False`, `flags: ['missing_git']`.

### Root cause

When a directory is registered as a git submodule, its `.git` entry is a
**file**, not a directory. The file contains one line:

```
gitdir: ../../../../.git/modules/SOLUTIONS/DevOps/SIDE-PROJECTS/ipscan
```

The actual git store lives at `<monorepo-root>/.git/modules/<submodule-name>/`.

`os.path.isdir('.git')` returns `False` for this file → every git-touching
code path skipped ipscan entirely.

### Fix

`_resolve_git_dir(path)` — a single-responsibility resolver that handles both:
- `.git` as a directory (normal repo)  
- `.git` as a file with `gitdir: <rel-path>` (submodule worktree)

All git-touching functions now go through this resolver.

### Lesson

**`os.path.isdir('.git')` is the wrong primitive for "is this a git repo".**
The correct check is: does `.git` exist (as file OR dir) AND can we resolve
a valid git store from it?

Submodule worktrees are a first-class git pattern. Any tool that inspects
repo structure must handle gitlink files or it will silently miss entire
categories of repos.

### New flag

`diagnose()` now returns `'submodule'` in `flags` when `.git` is a gitlink
file. Informational only — not an error. `health_ok` is `True` when the
submodule has a valid origin.

### R&D implications

- Track C (Submodule Hygiene) is now warranted — gitlink support is the
  foundation; workflow enforcement (hooks, manifest, drift detection) builds on it.
- `discover` should eventually support a `--submodules-only` filter to let
  operators quickly audit submodule health across the monorepo.
- Future `deliver` phase could auto-register orphaned `.git`-dir repos
  (currently: `clipd`, `redact`) as submodules if they have a known upstream.

---
