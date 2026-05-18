# pickaxe — Roadmap

> AS-IS vs TO-BE. What it does today vs where it's going.

---

## AS-IS — v0.1.0 (current)

pickaxe is a **discovery and scoring** tool. It does not touch git or GitHub — it only reads and reports.

**What it does:**

1. Walks a directory tree (respecting a configurable skip-list)
2. Reads the first 60 lines of each script file (`.py`, `.ps1`, `.sh`, `.rb`)
3. Extracts header metadata: `VERSION`, `CREATED`, `PURPOSE/ABSTRACT`, `LICENSE`, `SHEBANG`
4. Calls `git log --follow --oneline` to count commits per file
5. Scores each file on a 7-point scale (see [README § Scoring](README.md#scoring))
6. Outputs a ranked table (terminal) or Markdown report (`--output`)
7. For files with git history, **prints** (but does not run) the `git-filter-repo` command needed to extract them

**What it does NOT do:**

- Execute any git operations
- Handle whole subdirectories (only individual files)
- Preserve or migrate branches, tags, or releases
- Create remote repos
- Push anything

**Gap summary:**

| Capability | v0.1 |
|---|---|
| Find + score candidates | ✅ |
| Suggest extraction command | ✅ (prints it) |
| Execute extraction | ❌ |
| Subdir extraction (not just single files) | ❌ |
| Preserve branches / tags / releases | ❌ |
| Create remote repo | ❌ |
| Push extracted repo | ❌ |
| Dry-run mode | ❌ |
| Chain-of-custody audit trail (`.pickaxe/`) | ❌ |
| Detect + carry AI instruction files | ❌ |

---

## TO-BE — v0.2 (planned)

**Theme: full extraction pipeline, not just discovery.**

The core idea: when pickaxe finds a candidate, it should be able to complete the full workflow — from identifying the file or subdir in a monolith all the way to a new standalone repo on GitHub with its complete history intact.

### Subdir-aware extraction

Today, `git-filter-repo --path 'file.py'` extracts a single file. The next step is to recognize when a set of files should travel together (e.g., a `parsers/` subdir, a role, a module package) and emit `--path-glob 'subdir/**'` instead.

Pickaxe should detect candidate "clusters" — files in the same directory that share a parent history, similar authors, or a common `CREATED` date window — and suggest them as a unit.

### `.pickaxe/` — chain of custody

Every extraction leaves an audit trail on **both ends**.

**In the source monolith** (e.g., `automation/Windows/.pickaxe/`):
```
.pickaxe/
  extractions.md       ← log of every subdir carved out, when, to where
  scan-report.md       ← last pickaxe scan output for this repo
```

**In the destination repo** (e.g., `AAP-Chocolatey/.pickaxe/`):
```
.pickaxe/
  provenance.md        ← source repo, original path, date, commit range
  filter-repo.cmd      ← exact git-filter-repo command that was run
  original-paths.txt   ← pre-rename paths (needed if re-extraction is ever required)
  ai-instructions.md   ← which AI context files traveled with the extraction
```

This makes extractions reversible to audit, and gives future agents (and humans) full context on where a repo came from without hunting through git blame on a dead monolith.

### AI context detection

When extracting a subdir, pickaxe should detect and carry any AI instruction/context files from the surrounding tree:

- `.github/instructions/*.md` / `.github/copilot-instructions.md`
- `AGENTS.md` at any ancestor level
- `HANDOFF*.md` in the immediate parent
- Any file matching `AI.*.INSTRUCTIONS.md` (custom convention)

These are listed in `.pickaxe/ai-instructions.md` in the destination, with their original paths and a note on whether they were copied verbatim or referenced only.

**Real-world example:** `automation/Windows/helpers/tools/Chocolatey/c4b-v1.0.0/.github/instructions/ansible-c4b.instructions.md` lives above the `ansible/` subdir target and must travel with any extraction of that subdir.

### `--execute` mode

Add an execution pipeline that wraps the full workflow:

```
1. git clone <source_repo> <tmp_dir>
2. git -C <tmp_dir> filter-repo --path-glob '<target>/**' [--force]
3. Write <dest>/.pickaxe/provenance.md + filter-repo.cmd + original-paths.txt
4. Detect + copy AI context files → <dest>/.pickaxe/ai-instructions.md
5. Append to <source>/.pickaxe/extractions.md
6. gh repo create <org>/<new-name> --public
7. git -C <tmp_dir> remote add origin <new_remote>
8. git -C <tmp_dir> push --all --tags
```

`git-filter-repo` on a full clone preserves all branches and tags that touch the extracted path by default. The `--prune-empty` behavior should be opt-in, not default, to avoid losing merge context.

Flags:
- `--execute` — run the pipeline (default: dry-run only)
- `--org <name>` — GitHub org or user for new repos (default: from `gh auth status`)
- `--subdir` — treat candidate path as a directory glob, not a single file
- `--private` — create private repos instead of public
- `--no-push` — extract locally but do not create remote or push
- `--no-ai-context` — skip AI instruction file detection
- `--install-deps` — detect platform (macOS/Linux/Windows) and install `git-filter-repo` + `gh` via the appropriate package manager (`brew` / `pip` + package manager / `choco`)

### Dry-run output (enhanced)

Even without `--execute`, the report should emit a complete, copy-pasteable shell script per candidate — not just the filter-repo line, but the full 5-step pipeline above, parameterized and ready to run.

### Cluster detection

Group files into extraction clusters using heuristics:
- Same parent directory
- Same `CREATED` date (± 2 weeks)
- Same author
- Shared imports or function references (Python AST / PS1 dot-source scan)

Output a cluster summary before individual file scores.

### `--format json`

Emit the full candidate list as JSON for downstream piping into other tools (e.g., `converters`, a dashboard, a CI gate).

### `--since <date>`

Only score files modified (by git or mtime) after a given date. Useful for post-sprint cleanup runs.

### GitHub Actions integration

A pre-built workflow that runs `pickaxe --format json --min-score 4` on PR and posts a comment listing any new tool-worthy scripts detected in the changeset.

### Multi-repo index

Build a persistent catalog (JSON/SQLite) across multiple scanned repos. Query: *"show me all scripts across all my repos with score ≥ 5 that haven't been extracted yet."*

---

## Version plan

| Version | Theme | Key features |
|---|---|---|
| v0.1 *(current)* | Discovery | Score + suggest |
| v0.2 | Extraction | `--execute`, subdir mode, `.pickaxe/` chain-of-custody, AI context detection, full pipeline dry-run output |
| v0.3 | Clustering | Cluster detection, shared-history grouping |
| v0.4 | Automation | `--format json`, `--since`, GitHub Actions workflow |
| v1.0 | Catalog | Multi-repo index, persistent state, query interface |

---

*Roadmap authored 26-0518. Reference session: [HANDOFF.interrim-260518JN-Miners.md](../../projects/automation/AAP-NorthStar-Roadmap/HANDOFF.interrim-260518JN-Miners.md)*
