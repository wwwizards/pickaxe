# pickaxe

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Mine tool-worthy scripts from compound mono-repos.**

Scans a workspace directory tree, scores each script by how "tool-worthy" it is (has a shebang, version header, purpose block, few git commits = buried in the wrong repo), and outputs a ranked report with suggested `git-filter-repo` extraction commands for anything with history worth preserving.

> *"You don't lose your tools — you just forget where you put them."*

---

## Prerequisites

- Python 3.8+
- `git` in PATH (for commit-count scoring)
- `git-filter-repo` (for the suggested extraction commands — `brew install git-filter-repo`)

---

## Usage

```bash
# Quick table scan — print ranked candidates to terminal
python pickaxe.py ~/DATA/projects

# Full Markdown report with extraction commands
python pickaxe.py ~/DATA/projects --output pickaxe-report.md

# Lower the bar (score >= 2) to catch scripts without full headers
python pickaxe.py ~/DATA/projects --min-score 2

# Scan specific extensions only
python pickaxe.py ~/DATA/projects --extensions .py .ps1

# Dump everything regardless of score
python pickaxe.py ~/DATA/projects --all
```

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

| Field | Value |
|---|---|
| Score | 7 |
| Version | 0.9 |
| Created | 23-0713 |
| License | MIT |
| Git commits | 1 |

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

- [ ] `--format json` output for piping into other tools
- [ ] `--since <date>` — only score files modified after a date
- [ ] Auto-propose missing header blocks (inverted head2md)
- [ ] GitHub Actions integration: run on PR to flag new tool-worthy scripts
- [ ] Multi-repo index: build a searchable catalog across all miners

---

## License

[MIT](LICENSE) © 2026 [wwwizards](https://github.com/wwwizards)

---

*This file was documented by the tool it documents. 🪨⛏️*
