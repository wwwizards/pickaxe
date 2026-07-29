# PICKAXE

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Portable Independent Collaborative-Knowledge AjaX-Extender**

**Mine tool-worthy scripts from compound mono-repos. Inspect repo health. Analyze commit cadence. Replicate knowledge across federated nodes — no message queues, no clusters, no containers.**

Scans a workspace directory tree, scores each script by how "tool-worthy" it is (has a shebang, version header, purpose block, few git commits = buried in the wrong repo), and outputs a ranked report with suggested `git-filter-repo` extraction commands for anything with history worth preserving.

> *"You don't lose your tools — you just forget where you put them."*

---

## Prerequisites

### v0.1 — discovery mode

| Dependency | Purpose | Install |
|---|---|---|
| Python 3.8+ | runs the script | pre-installed on macOS |
| `git` | commit-count scoring (`git log --follow`) | pre-installed |
| `git-filter-repo` | suggested extraction commands are printed but **not executed** | `brew install git-filter-repo` |

No `pip install` required — stdlib only.

### Optional

| Dependency | Purpose | Install |
|---|---|---|
| `holidays` | annotate commit-trends output with national holidays | `pip install holidays` |

### v0.2 — execute mode (planned)

Adds two runtime requirements on top of the above:

| Dependency | Purpose | Install |
|---|---|---|
| `git-filter-repo` | **actually runs** the extraction (required, not just suggested) | macOS: `brew install git-filter-repo` · Linux: `pip install git-filter-repo` |
| `gh` CLI | creates the remote repo (`gh repo create`) | macOS: `brew install gh` · Linux/Windows: see [cli.github.com](https://cli.github.com) · then `gh auth login` |

---

## Usage

### Repo health — discover & diagnose

```bash
# Map all git repos under a root (health, remote, branch)
python pickaxe.py discover ~/DATA/projects

# JSON output for piping
python pickaxe.py discover ~/DATA/projects --format json

# Inspect a single repo's health
python pickaxe.py diagnose ~/DATA/projects/my-tool
```

### Commit cadence — discover commit-trends

```bash
# Weekly cadence for the repo at cwd (default)
python pickaxe.py discover commit-trends

# Specific repo, daily granularity
python pickaxe.py discover commit-trends --repo ~/DATA/projects/my-tool --by day

# Monthly, date-range filtered
python pickaxe.py discover commit-trends --by month --from 2026-01-01 --to 2026-06-30

# Lower the marathon threshold (default: >2 commits/week)
python pickaxe.py discover commit-trends --marathon-threshold 5

# Annotate with US holidays (requires: pip install holidays)
python pickaxe.py discover commit-trends --holidays us

# JSON output
python pickaxe.py discover commit-trends --format json

# Save session event to .pickaxe/SESSIONS/
python pickaxe.py discover commit-trends --save
```

### Remote drift — `discover drift`

`pickaxe discover drift` fetches all remotes and reports ahead/behind/dirty per repo — the AS-IS git health map across the entire workspace.

```bash
# Show all repos: ahead commits (push-needed), behind commits, uncommitted files
python pickaxe.py discover drift ~/DATA/projects

# From current directory
python pickaxe.py discover drift .

# Machine-readable output
python pickaxe.py discover drift ~/DATA/projects --format json
```

Output columns:

| Column | Meaning |
|--------|---------|
| `AHEAD` | Local commits not yet pushed to origin |
| `BEHIND` | Remote commits not yet pulled |
| `DIRTY` | Uncommitted modified/untracked files |
| `FLAGS` | `push-needed` \| `behind` \| `uncommitted` \| `no-remote` \| `fetch-failed` |

Repos flagged `no-remote` have no origin configured — they exist only on disk (and in any pickaxe backup).

### Instruction bloat — `diagnose instruction-bloat` & `deliver instruction-rollup`

`pickaxe diagnose instruction-bloat` scans instruction/handoff/memory files for the 200-line reliability threshold (per the [200-line reliability rule](https://github.com/wwwizards/ai-labs)) and reports oversized files plus oversized sections within them. `pickaxe deliver instruction-rollup` consumes that report and extracts oversized sections into scoped child files, leaving a pointer stub in the original — dry-run by default, `--execute` to write.

```bash
# Report oversized instruction files (dry-run, read-only)
python pickaxe.py diagnose instruction-bloat ~/DATA/projects --format json --save

# Pipe findings into a rollup plan
python pickaxe.py diagnose instruction-bloat . --format json > findings.json
python pickaxe.py deliver instruction-rollup . --from-report findings.json

# Actually write the extracted files + pointer stubs
python pickaxe.py deliver instruction-rollup . --from-report findings.json --execute
```

```bash
# Quick table scan — print ranked candidates to terminal
python pickaxe.py scan ~/DATA/projects

# Full Markdown report with extraction commands
python pickaxe.py scan ~/DATA/projects --output pickaxe-report.md

# Lower the bar (score >= 2) to catch scripts without full headers
python pickaxe.py scan ~/DATA/projects --min-score 2

# Scan specific extensions only
python pickaxe.py scan ~/DATA/projects --extensions .py .ps1

# Dump everything regardless of score
python pickaxe.py scan ~/DATA/projects --all
```

### Backup & restore

`pickaxe backup` snapshots every git repo under a root into a portable backup directory — safe to copy to OneDrive, a NAS, or any cloud storage.

**What it creates:**

```
<dest>/
  manifest.json          # repo inventory: paths, remotes, branches, bundle status
  bundles/
    root.bundle          # monorepo committed history
    SOLUTIONS__...bundle # one bundle per discovered submodule/repo
  working-tree/          # full file copy (no .git dirs) — captures uncommitted changes
```

```bash
# Backup workspace root to a named snapshot dir
python pickaxe.py backup ~/DATA/projects --to ~/backups/LW-260721

# Bundles only — skip working-tree copy (faster; use when all changes are committed)
python pickaxe.py backup ~/DATA/projects --to ~/backups/LW-260721 --skip-working-tree

# JSON output (pipe into other tools)
python pickaxe.py backup . --to ~/backups/LW-260721 --format json

# Restore repos from a backup (git clone from each bundle, re-adds origin remote)
python pickaxe.py restore ~/backups/LW-260721 --to ~/restored

# Restore with JSON output to inspect results
python pickaxe.py restore ~/backups/LW-260721 --to ~/restored --format json
```

**Restore behaviour:**

| Status | Meaning |
|---|---|
| `ok` | Cloned from bundle; origin remote re-added if known |
| `already_exists` | Target path exists — skipped (safe to re-run) |
| `missing_bundle` | Bundle file absent from backup dir |
| `clone_failed` | `git clone` returned non-zero |

> **Tip:** For a pre-BIOS/pre-migration safety snapshot, combine backup with an OS-level copy:
> `robocopy ~/DATA/projects ~/backups/LW-260721/working-tree /E /SL` captures symlinks that `shutil.copytree` may not preserve on all platforms.

---

## Scoring

Each script earns points toward its extraction score:

| Signal | Points | Meaning |
|---|---|---|
| Has shebang (`#!/usr/bin/env`) | +1 | Intended to run standalone |
| Has `VERSION:` header field | +2 | Author tracked versions intentionally |
| Has `CREATED:` date | +1 | Lineage is documented |
| Has `PURPOSE:` or `ABSTRACT:` | +1 | Intent is clear |
| Has `LICENSE:` field | +1 | Author thought about open-sourcing |
| 1–3 git commits (mono-repo squatter) | +1 | Doesn't belong here |

**Default threshold:** `--min-score 3`. Good for repos with the [autodoc header convention](https://github.com/wwwizards/autodoc). Drop to `2` for stranger codebases.

---

## Sample output (terminal)

```
SCORE  COMMITS   VERSION  PATH
-----  -------  --------  ------------------------------------------------------------
    7        1      0.9   automation/tools/scripts/python/ipscan.py
    7        2      0.6.1 pipeline-tools/helpers/general/autoDoc/head2md.py
    6        1      0.3.1 tools/scripts/python/converters/convert_from_json.py
    5        1      0.1.0 scriptlets/parse_ns_services-v0.2.py
```

---

## Sample report (Markdown)

The `--output` flag writes a full Markdown report including extraction commands:

````markdown
## `automation/tools/scripts/python/ipscan.py`

| Field       | Value   |
| ----------- | ------- |
| Score       | 7       |
| Version     | 0.9     |
| Created     | 23-0713 |
| License     | MIT     |
| Git commits | 1       |

**History worth preserving (1 commit):**
```bash
git clone /path/to/automation /tmp/extracted-repo
git -C /tmp/extracted-repo filter-repo --path 'tools/scripts/python/ipscan.py' --force
```
````

---

## The autodoc header convention

pickaxe scores highest when files follow the inline header format from [wwwizards/autodoc](https://github.com/wwwizards/autodoc):

```python
# --------------------------------------------------------------------------
# SCRIPT: my_tool.py
# --------------------------------------------------------------------------
# PURPOSE: What this does in one sentence.
# LICENSE: MIT - https://opensource.org/licenses/MIT
# CREATED: YYYY-MM-DD BY: Author Name <email>
# UPDATED: YYYY-MM-DD BY: Author Name <email> - what changed
# VERSION: v1.0.0
# AUTODOC: https://github.com/wwwizards/pickaxe
# --------------------------------------------------------------------------
```

The `AUTODOC:` field closes the loop — it tells pickaxe (and future readers) how this file was found and documented.

---

## Roadmap

> Full AS-IS vs TO-BE breakdown, feature spec, and version plan: **[ROADMAP.md](ROADMAP.md)**

- [x] `discover` — repo health map (path, remote, branch, flags)
- [x] `diagnose` — single-repo health inspection
- [x] `discover commit-trends` — weekly/daily/monthly cadence, marathon detection, date range, holiday annotation
- [x] `backup` — bundle all repos + working-tree snapshot to portable dir; `manifest.json` inventory
- [x] `restore` — restore repos from pickaxe backup; re-attaches origin remotes
- [x] `discover drift` — fetch + ahead/behind/dirty per repo; flags push-needed/behind/uncommitted/no-remote
- [x] `diagnose instruction-bloat` — flag instruction/handoff files over the 200-line reliability threshold
- [x] `deliver instruction-rollup` — extract oversized instruction sections into scoped children + pointer stub (dry-run by default, `--execute` to write)
- [ ] `deliver drift` — apply fixes from drift report
- [ ] `--execute` — full git-filter-repo extraction pipeline
- [ ] GitHub Actions integration: run on PR to flag new tool-worthy scripts
- [ ] Multi-repo index: build a searchable catalog across all miners

---

## License

[MIT](LICENSE) © 2026 [wwwizards](https://github.com/wwwizards)

---

*This file was documented by the tool it documents. 🪨⛏️*
