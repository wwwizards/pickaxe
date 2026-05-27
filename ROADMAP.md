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

### Standalone-repo detection (skip already-extracted)

Pickaxe v0.1 has no awareness of whether a candidate is already a standalone repo — it will score and suggest extraction for files that live inside a git submodule or are already cloned into the monorepo from their own remote. This produces false positives.

v0.2 should detect and skip (or annotate) candidates that:
- Have a `.git/` directory at or above their immediate parent inside the scan tree
- Report a `git remote` that differs from the root monorepo's origin

Output should annotate these as `[already extracted → <remote>]` rather than omitting them silently, so the operator can confirm the extraction happened and audit the pointer.

**Field observation (LogicWizards scan, 2026-05-18):** `psst`, `psstel`, `clipd`, `redact`, `pickaxe` itself all scored 6–7 and appeared as extraction candidates despite having their own repos at `wwwizards/*`. This is the primary source of false positives in mixed monorepo+submodule layouts.

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

## Roadmap Checklist (Execution Tracker)

Use this as the live execution sheet for development and handoff continuity.

### Track A — Extraction foundation

- [ ] `v0.2` pipeline runner ships with `--execute`, `--no-push`, `--private`, and `--subdir`
- [ ] `.pickaxe/` chain-of-custody files are emitted on destination repo (`provenance.md`, `filter-repo.cmd`, `original-paths.txt`, `ai-instructions.md`)
- [ ] source-repo extraction log appends reliably to `.pickaxe/extractions.md`
- [ ] AI instruction detection supports `.github/*`, `AGENTS.md`, and `HANDOFF*.md`
- [ ] dry-run script output is complete and copy-paste runnable

### Track B — Repo hygiene and drift control

- [ ] `pickaxe doctor` identifies repo state anomalies (missing `.git`, missing `origin`, stripped `.git/config`)
- [ ] `pickaxe inventory` emits local repo map (path, remote, branch, health flags)
- [ ] `pickaxe hydrate` can clone missing repos and restore missing remotes from a canonical manifest
- [ ] `pickaxe drift` compares local inventory vs canonical GitHub set and reports mismatches
- [ ] `pickaxe provision` applies baseline repo hygiene files (RFC-002 path)
- [ ] `pickaxe report` writes timestamped remediation report (Markdown + JSON)

### Track C — Context oracle

- [ ] Lightbulb Log query adapter reads ai-labs anti-pattern corpus
- [ ] canonical tool inventory and provenance model is queryable
- [ ] public registry probes (Chocolatey, PSGallery, Ansible Galaxy) return actionable existence checks
- [ ] `pickaxe audit` outputs agent-agnostic handoff guidance with recommended/no-op verdict
- [ ] engagement opener template finalized for human + agent consumers

### Done criteria by milestone

- [ ] `v0.2` done: extraction pipeline runs end-to-end on at least one real carve-out
- [ ] `v0.4` done: hygiene + drift commands catch and remediate missing repo/remote state
- [ ] `v0.6` done: local code scan + ai-labs query produces a non-trivial reuse recommendation
- [ ] `v1.0` done: context-oracle flow can answer "do I need to build this?" with provenance-backed evidence

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

## North Star — The Context Oracle (2026-05-26)

*What pickaxe is really for.*

Chocolatey and Ansible Galaxy are not tools — they are community-driven libraries. Their value is not the packaging system or the automation engine. It is the accumulated knowledge of thousands of contributors who already answered *"is there a better way to do this?"* so the next person does not have to. A Chocolatey package is distilled community knowledge. An Ansible role is a tested, peer-reviewed answer to a problem you were about to solve from scratch.

**pickaxe is the same pattern applied to AI-assisted DevOps knowledge.**

The problem it solves: when someone encounters code they do not understand, they feed it to ChatGPT and get back a "working" variant that ignores three years of hard-won lessons baked into the original. That variant gets deployed to PROD. It fails in the exact scenario the original solved, 18 months later. The org now has N snowflakes, nobody knows which is canonical, and the original author gets called in to fix the worst one. This is not a people problem. It is a *context-travel* problem: the tool shipped without its behavioral history, anti-pattern library, and "don't touch this" guardrails.

**The question pickaxe answers at the point of decision:**

> "Before you fork, extend, or ChatGPT this — here is what you need to know, here is what has already been tried, here is whether this capability already exists, and here is whether you actually need to do anything at all."

Most of the time the answer is: you don't.

### The three sources pickaxe queries

| Source | Answers |
|---|---|
| **ai-labs Lightbulb Log** | "This pattern has been tried. Here is what happened and when." |
| **Canonical tool inventory + provenance** | "This capability already exists in tool X at version Y. Use it." |
| **Public registries** (Chocolatey, Ansible Galaxy, PSGallery, etc.) | "This package already does that. Install it instead." |

### The output

Not a diff. Not a lint report. **Agent-agnostic handoff instructions** — markdown that works whether the consumer is GitHub Copilot, Claude, ChatGPT, or a junior sysadmin who has never seen the codebase. The format does not matter because it travels as prose.

The "you probably do not need to extend it" verdict is the killer feature — the same discipline experienced engineers apply before writing a custom installer, but automated and available to anyone at `pickaxe audit`.

### The ecosystem

```
ai-labs      → the knowledge base (Lightbulb Log, observations, anti-patterns, RFCs)
pickaxe      → the query engine that applies that knowledge to live code
RFC-002      → the repo hygiene standard pickaxe enforces
RFC-003      → the context oracle protocol pickaxe implements
```

The community contribution model makes this compound: one org's Lightbulb Log entry is another org's avoided 3-hour rabbit hole. The library grows with every incident. That is the Chocolatey model applied to DevOps wisdom instead of software packages.

### Implications for the version plan

v0.2 and v0.3 (extraction, clustering) remain valid — they are the *foundation* pickaxe needs before it can be a context oracle. You cannot query provenance you have not recorded. v0.4+ shifts from "automation" to "knowledge integration":

| Version | Theme | North Star connection |
|---|---|---|
| v0.2 | Extraction | Records provenance — makes query possible |
| v0.3 | Clustering | Groups related tools — reduces false positives |
| v0.4 | Hygiene | `pickaxe provision` — repo baseline enforcement (RFC-002) |
| v0.5 | Fork detection | Finds downstream copies, scores drift from canonical |
| v0.6 | Knowledge query | Queries ai-labs Lightbulb Log against live code |
| v1.0 | Context oracle | `pickaxe audit` — full engagement-opener report |

---

*Roadmap authored 26-0518. North Star added 26-0526.* *Reference session: [HANDOFF.interrim-260518JN-Miners.md](../../projects/automation/AAP-NorthStar-Roadmap/HANDOFF.interrim-260518JN-Miners.md)*
