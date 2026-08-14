# pickaxe — Roadmap

```
# --------------------------------------------------------------------------
# NOTES:    ROADMAP.md
# --------------------------------------------------------------------------
# ABSTRACT: AS-IS capabilities and staged delivery plan for the pickaxe CLI.
# CREATED:  260612 BY: LogicWizards.NYC
# UPDATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - A1-A4 shipped (noun-dispatch, deliver verb, instruction-bloat, instruction-rollup), 119 tests green
# UPDATED:  260730 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - LB-03/LB-04 fixes (data-loss + dest-routing), root-repo dogfood validation, 123 tests green
# UPDATED:  260809 BY: ALICE::Copilot::ai-labs.SOLOMON - added `diagnose tasks-bloat` host-specific-adapter idea (TO-BE), companion to ai-labs-toolkit PROTOCOL.md
# UPDATED:  260814 BY: SOLOMON(Sonnet5)::Copilot::ai-labs.WIZ-00.fleet - flagged `pyst` as a concrete Track A cluster-extraction candidate (no code changed)
# ARCHITECT: Joe Negron -- LogicWizards.NYC
# TECHLEAD:  JN (Joe Negron -- LogicWizards.NYC)
# VERSION:  0.4.2  (mirrors the pickaxe CLI's shipped version — this file
#           IS the canonical version record; pickaxe.py has no __version__
#           constant. ALL .HANDOFF docs now mirror this same number and
#           bump together at every wrap — no separate per-doc revision
#           cadence, per 2026-07-29 decision.)
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```

> AS-IS vs TO-BE. What it does today vs where it's going.

---

## AS-IS — v0.4.1 (current, reconciled 2026-07-29)

pickaxe is a **discovery, diagnostic, backup, and delivery** tool with a real 5D command surface (`discover`, `diagnose`, `deliver`, `scan`, `backup`, `restore`). It does not yet rewrite git history, create remotes, or push — extraction (Track A) remains 100% unbuilt. Ground-truthed this session against `pickaxe.py`'s actual `argparse` subcommands, `git log --oneline`, and a live run: `python -m pytest test_pickaxe.py -q` → **123 passed**, 2026-07-30 (v0.4.2 adds LB-04 dest-routing fix + regression tests on top of v0.4.1's LB-03 data-loss fix).

**Shipped commands (verified against source + tests, not just docs):**

| Command | What it does | Shipped |
|---|---|---|
| `pickaxe discover [root]` | repo map: path/rel/remote/branch/flags/health_ok; `--submodules-only` filters to gitlink entries | v0.2.0 (260612); `--submodules-only` v0.3.4 |
| `pickaxe discover commit-trends` | weekly/daily/monthly commit cadence, `--marathon-threshold`, `--holidays us`, `--save` | v0.3.3 (260615) |
| `pickaxe discover drift [root]` | AHEAD/BEHIND/DIRTY/FLAGS table (`push-needed`\|`behind`\|`uncommitted`\|`no-remote`\|`fetch-failed`) | v0.3.6 |
| `pickaxe diagnose [path]` | single-repo health: `missing_git`\|`missing_origin`\|`stripped_config`; gitlink/submodule-aware | v0.2.0; gitlink fix v0.3.2 (260603) |
| `pickaxe diagnose instruction-bloat [root]` | noun-dispatch retrofit (A1) + whole-file/section line-threshold scan of instruction files (`--max-lines` 1000, `--max-section-lines` 50) (A3) | v0.4.0 (260729) |
| `pickaxe deliver instruction-rollup <root> --from-report <findings.json> [--execute]` | first-ever `deliver` verb (A2); dry-run plan by default, extracts flagged blocks into new `.instructions.md` files with auto-filled frontmatter, idempotent (A4); overlapping whole-file+section findings now reported `skipped_overlap` (LB-03 fix); `.github/` sources route to `.github/instructions/` for VS Code auto-discovery (LB-04 fix) | v0.4.0 (260729); LB-03 fix v0.4.1 (260729); LB-04 fix v0.4.2 (260729) |
| `pickaxe scan [root]` | tool-worthiness scorer (header metadata, commit count, 7-point scale); `already_extracted` annotation | v0.1.0 scorer; annotation v0.3.4 |
| `pickaxe backup <root> --to <dest>` | snapshot all repos (bundles + working-tree) to a portable backup dir; `--skip-working-tree`, `--force` | v0.3.5 |
| `pickaxe restore <backup> --to <dest>` | restore repos from a pickaxe backup manifest | v0.3.5 |

All commands support `--format table\|json`; all except `restore` support `--save` (session event under `.pickaxe/SESSIONS/`).

**What it does NOT do (real gaps — Track A/C/D/E):**

- Execute any git-history-rewriting operation (`git-filter-repo`) — still only ever printed, never run
- Handle subdir/cluster extraction as a unit (only single-file `scan` scoring exists)
- Preserve branches/tags/releases through an extraction (no extraction path exists yet to test this against)
- Create a remote repo or push anything (`gh repo create`, `git push`) — zero GitHub write access
- Emit or read `.pickaxe/` chain-of-custody files (`provenance.md`, `filter-repo.cmd`, `extractions.md`) — schema designed, not implemented
- Detect + carry AI instruction files during an extraction — designed, not implemented
- Any Track C context-oracle query (Lightbulb Log lookup, tool inventory, public registry probe)
- Any Track D MQL/persona verb (`pickaxe MATT seek ...`) or git-passthrough (`push`/`pull`/`fetch`/`status <name>`)
- Any Track E manifest command (`discover tools`, `sync`, `context resolve`) — `AI-TRAINING-MANIFEST.md` v0.1.0 contract is design-only per `.HANDOFF/STATE.md`

**Gap summary:**

| Capability                                      | v0.4.0                    |
|--------------------------------------------------|---------------------------|
| Find + score candidates (`scan`)                  | ✅                          |
| Repo health map + drift (`discover`, `diagnose`)  | ✅                          |
| Instruction-bloat diagnostic + rollup delivery (`diagnose`/`deliver`) | ✅ (A1-A4) |
| Backup / restore whole workspace                  | ✅                          |
| Commit-cadence analytics                          | ✅                          |
| Suggest extraction command                        | ✅ (prints it)              |
| Execute extraction (`--execute`)                  | ❌                          |
| Subdir/cluster extraction                         | ❌                          |
| Preserve branches / tags / releases               | ❌ (untested — no path yet) |
| Create remote repo / push                         | ❌                          |
| Chain-of-custody audit trail (`.pickaxe/`)        | ❌                          |
| Detect + carry AI instruction files                | ❌                          |
| Context oracle (Track C)                          | ❌ (design only)            |
| MQL / persona delegation (Track D)                | ❌ (design only)            |
| Manifest sync (Track E)                           | ❌ (design only)            |

> **Reconciliation note (2026-07-29):** this section previously read "v0.1.0 (current)" while the file's own header (`VERSION: 0.3.2`→`0.3.4`) and `.HANDOFF/STATE.md` already tracked v0.3.4 → v0.3.6 shipped — a multi-version documentation drift, the same failure class as the proposed `diagnose ticket-drift` (see Track B). Fixed by ground-truthing against source + a live test run rather than trusting prior prose. See also [`.HANDOFF/STATE.md`](.HANDOFF/STATE.md) "Shipped baseline" for the full per-version changelog this table summarizes.

## Cross-referenced tickets (Agile-Wizard)

These Agile-Wizard tickets reference specific pickaxe capabilities (shipped or planned) directly — checked here so roadmap work doesn't silently diverge from what a ticket already promised or assumed:

- [NEW-260107-AutoExec-A1S03-STORY-Add-Requires-Frontmatter-5-Instructions](../../Agile-Wizard/DATA/LogicWizards-NYC/Idea-Map/STORIES/NEW-260107-AutoExec-A1S03-STORY-Add-Requires-Frontmatter-5-Instructions.md) — cites the exact `diagnose ticket-drift` evidence (0/5 vs actual 5/5 done) used as this candidate's justification below in Track B.
- [NEW-260528-IntuneDeployments-C1S03-STORY-ART-Repo-Split-Pre-Scaffold](../../Agile-Wizard/DATA/Phoenix-CPAs/BACKLOG/NEW-260528-IntuneDeployments-C1S03-STORY-ART-Repo-Split-Pre-Scaffold.md) — assumes a `repos.manifest.json` entry stub and a pickaxe `deliver` command for manifest-driven clone post-split; both remain unbuilt (Track B backlog, `PX-01`/`PX-03` in `.HANDOFF/STATE.md`) — flagged so that STORY's acceptance criteria aren't checked off against tooling that doesn't exist yet.

### Dogfood validation: root `.github/copilot-instructions.md` (2026-07-30)

A manual "crawl before walk" trim of the repo's own live instructions file (1134 → 1036
lines, -8.6%, two safe cuts: dead terminal-strategy history + duplicated release history)
was cross-checked against `pickaxe diagnose instruction-bloat .`. Result: the scanner
**already flags every section a human found by hand**, with zero new detection logic
needed:

| Section | Lines | Flagged by pickaxe |
|---|---|---|
| Whole file | 1036 (>1000) | ✅ |
| `TDD Guardrails (MANDATORY)` | 104 | ✅ |
| `Conventions & patterns (project-specific)` | 103 | ✅ |
| `Validation Scripts Testing Standard (MANDATORY)` | 112 | ✅ |
| `Proactive Context Optimization (MANDATORY)` | 53 | ✅ |
| `Proactive Agile Governance (MANDATORY)` | 126 (largest single section) | ✅ |
| `Agile-DevOps Workflow` | 54 | ✅ |

Both `Proactive-*` blocks trace to 2025-11-23 (`git log -S`), essentially the file's
founding week — they were among the first rules ever written for this repo, not recent
additions. `Proactive Agile Governance` references Idea-Map (still live/current per
260+ workspace hits and the 2026-05-27 handoff) but is 126 lines of MANDATORY prompt
template — a strong candidate for the next controlled trial of `deliver
instruction-rollup`, since detection is already proven correct here.

**Implication:** the blocker to using pickaxe as the "force multiplier" the manual crawl
was building toward isn't tooling capability — it's confidence, after a prior
`--execute` run on this same file was reverted earlier in this repo's history. Next
step is a controlled dry-run comparison (no `--execute`) against these 6 known-good
targets before re-attempting a live rollup. See
[`instructions-bloat-backlog.md`](/memories/repo/instructions-bloat-backlog.md) (repo
memory, root workspace) for full session notes.

---

## TO-BE — Track A: Extraction Pipeline (not started — no version shipped)

*Renamed from "v0.2 (planned)". The actual version numbers v0.2.0 through v0.3.6 all shipped under Track B (repo hygiene/drift) instead — see the Version plan reconciliation note below. Track A has never shipped anything; everything in this section remains 100% aspirational.*

**Theme: full extraction pipeline, not just discovery.**

The core idea: when pickaxe finds a candidate, it should be able to complete the full workflow — from identifying the file or subdir in a monolith all the way to a new standalone repo on GitHub with its complete history intact.

### Subdir-aware extractions

Today, `git-filter-repo --path 'file.py'` extracts a single file. The next step is to recognize when a set of files should travel together (e.g., a `parsers/` subdir, a role, a module package) and emit `--path-glob 'subdir/**'` instead.

Pickaxe should detect candidate "clusters" — files in the same directory that share a parent history, similar authors, or a common `CREATED` date window — and suggest them as a unit.

**Concrete near-term candidate (flagged 2026-08-14):** `pyst` (`SOLUTIONS/DevOps/SIDE-PROJECTS/ipscan/pyst.py` + its `test_pyst_*.py` companions) is an ART-pattern tool born inside `ipscan` that has outgrown it — targeted for feature/UX parity with `psst` first, then extraction via this very Track A pipeline (destination: own repo, or a sibling module inside the `psst` repo — undecided). A live example of exactly the cluster-detection problem this section describes, once Track A exists. Cross-referenced: root `.HANDOFF/STATE.md` (PINNED), `ipscan/README.md` Roadmap, `psst/ROADMAP.md`.

### Submodule Aware Commits

Following standard protocol — we start with the mandatory discovery: read STATE.md and run the SYNC-BEFORE-WRAP git checks (fetch, divergence, submodules, what's staged). With that, 

1. in order to discover the current state of any monorepo, we must first check for submodules & branch divergence with something like this: 

`
cd C:\PROJECTS\LogicWizards; Write-Host '=== SUBMODULES ==='; git submodule status; Write-Host '=== CURRENT BRANCH + DIVERGENCE ==='; git branch --show-current; git fetch origin --prune 2>&1 | Out-String; git rev-list --left-right --count HEAD...origin/master 2>&1 | Out-String; Write-Host '=== STAGED (name-status) ==='; git --no-pager diff --cached --name-status; Write-Host '=== UNSTAGED / UNTRACKED (short) ==='; git status --short
`

2. then we need to check previous commits to comply with our `SYNC-BEFORE-WRAP` gate to 

`
Write-Host '=== LAST 8 RELEASE COMMITS ==='; git --no-pager log --oneline -8; Write-Host '=== HIGHEST v0.7.8.x IN HISTORY ==='; git --no-pager log --all --oneline | Select-String 'v0\.7\.8\.\d+' | Select-Object -First 5; Write-Host '=== HIGHEST COMMIT-MSG FILE ==='; Get-ChildItem COMMIT-MSG-v0.7.8.*.txt | ForEach-Object { if ($_.Name -match 'v0\.7\.8\.(\d+)') {[pscustomobject]@{N=[int]$Matches[1];Name=$_.Name}} } | Sort-Object N -Desc | Select-Object -First 3; Write-Host '=== SUBMODULE DIRTY DETAIL (pickaxe) ==='; git -C SOLUTIONS/DevOps/SIDE-PROJECTS/pickaxe status --short; Write-Host '=== SUBMODULE DIRTY DETAIL (ai-labs-toolkit) ==='; git -C SOLUTIONS/DevOps/SIDE-PROJECTS/vsCode/ai-labs-toolkit status --short
`
> :important: NOTE: the above examples use the LogicWizards directory but can  represent any workspace-root-dir in vscode. 

Per the `SUBMODULES ARE NOT THE MONOREPO` gate, submodule pointer bumps must never ride along in an unrelated subdir wrap — each submodule commits to its own remote first, then its parent pointer is bumped in a dedicated commit. Those two submodules have live in-progress work that their own agents/sessions need to wrap separately.

3. once that is complete we check that there are no extraneous line wraps in md files and check that the meta-h
eaders are in order for fsDB/fsQL compiance

` Write-Host '=== HEADER CHECK ==='; python 'SOLUTIONS\DevOps\SIDE-PROJECTS\ai-labs\experiments\autodocs\check-headers.py' '.HANDOFF\STATE.md' 'SOLUTIONS\CloudOps\Intune-Deployments\.HANDOFF\STATE.md'; Write-Host '=== STAGE WRAP DOCS ==='; git add 'COMMIT-MSG-v0.7.8.100.txt' '.HANDOFF/STATE.md' 'SOLUTIONS/CloudOps/Intune-Deployments/.HANDOFF/STATE.md'; Write-Host '=== FINAL STAGED SET ==='; git --no-pager diff --cached --stat; Write-Host '=== NOT STAGED (should be dirt only) ==='; git status --short | Select-String -NotMatch 'Intune-Deployments'`

we need to do similar things on every commit dso iwould loove to make this ceremony more generic and have pickaxe do those things instead of agents - to minimize token spend...

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

**Status (2026-07-29):** the *annotation* (`already_extracted` field, `[extracted → <remote>]` label) shipped in v0.3.4 under Track B — see AS-IS above. The *skip-by-default/exclude* behavior described in this section is still TO-BE: v0.3.4 annotates candidates, it does not omit them.

### Cluster detection

Group files into extraction clusters using heuristics:
- Same parent directory
- Same `CREATED` date (± 2 weeks)
- Same author
- Shared imports or function references (Python AST / PS1 dot-source scan)

Output a cluster summary before individual file scores.

### `--format json` ✅ shipped v0.3.3 (Track B, not Track A)

*Kept here for narrative continuity with the original plan text — this shipped early, under Track B, not as part of this (still unbuilt) extraction pipeline.* Emit the full candidate list as JSON for downstream piping into other tools (e.g., `converters`, a dashboard, a CI gate). Supported on `scan`, `discover`, and `discover commit-trends`. `already_extracted` field included in scan JSON output (v0.3.4).

### `--since <date>`

Only score files modified (by git or mtime) after a given date. Useful for post-sprint cleanup runs.

### GitHub Actions integration

A pre-built workflow that runs `pickaxe --format json --min-score 4` on PR and posts a comment listing any new tool-worthy scripts detected in the changeset.

### Multi-repo index

Build a persistent catalog (JSON/SQLite) across multiple scanned repos. Query: *"show me all scripts across all my repos with score ≥ 5 that haven't been extracted yet."*

### `diagnose tasks-bloat` (host-specific adapter, idea 2026-08-09)

Flag drift in VS Code `.vscode/tasks.json` the way `diagnose instruction-bloat` flags oversized instruction files: transient/scratch entries (created by `create_and_run_task` and never cleaned), duplicates, version-pinned one-offs (e.g. `Publish v0.7.8.87 Repository Chain`), and non-portable absolute-path commands. Because pickaxe is deliberately tool-agnostic and portable while `tasks.json` is a VS Code construct, this belongs as an opt-in **host-specific adapter**, not core. Companion context: the [ai-labs-toolkit PROTOCOL](../vsCode/ai-labs-toolkit/PROTOCOL.md) documents why the toolkit is the primary generator of scratch tasks, so the two tools pair naturally — the toolkit owns terminal transport, pickaxe owns the hygiene reporting.

---

## Roadmap Checklist (Execution Tracker)

Use this as the live execution sheet for development and handoff continuity.

### Track A — Extraction foundation

*Unscheduled version slot — see Version plan reconciliation note. Zero items shipped as of 2026-07-29.*

- [ ] pipeline runner ships with `--execute`, `--no-push`, `--private`, and `--subdir`
- [ ] `.pickaxe/` chain-of-custody files are emitted on destination repo (`provenance.md`, `filter-repo.cmd`, `original-paths.txt`, `ai-instructions.md`)
- [ ] source-repo extraction log appends reliably to `.pickaxe/extractions.md`
- [ ] AI instruction detection supports `.github/*`, `AGENTS.md`, and `HANDOFF*.md`
- [ ] dry-run script output is complete and copy-paste runnable

### Track B — Repo hygiene and drift control

Commands follow the 5D surface. See `.HANDOFF/DESIGN.md` for full mapping.

- [x] `pickaxe diagnose` — identifies repo state anomalies (missing `.git`, missing `origin`, stripped `.git/config`)
- [ ] `pickaxe diagnose` venv/dependency-tree detection — scan workspaces for common large dependency trees (`.venv/`, `venv/`, `env/`, `node_modules/`, `__pypackages__/`) and compare them with the nearest VS Code `settings.json` entries for `files.watcherExclude`, `files.exclude`, `search.exclude`, and `github.copilot.chat.codeSearch.fileExcludePatterns`. Emit a `dependency_tree_unexcluded` warning with directory name, file count, and missing exclusion surfaces. Rationale: `.venv` accounted for 28,370 of 30,161 workspace files (94%) on this machine while one Extension Host reached 3,162 MB. After exclusions, a VS Code update, reboot, and Python/Pylance extension removal, all Extension Hosts stabilized at 595 MB (81.2% lower), CPU remained in the low 20% range, and overall RAM remained approximately 50% lower. The result demonstrates combined recovery; it does not isolate a single cause. Docs: `.AI-TRAINING/GPU-VsCode-TroublleShooting-101.md`.
- [x] `pickaxe discover` — emits local repo map (path, remote, branch, health flags); default output `table`, `--format json` for piping
- [x] `pickaxe discover commit-trends` — weekly (or daily/monthly) commit cadence for any repo; marathon detection (>2 commits/week by default, configurable); `--from`/`--to` date range; `--by week|day|month`; `--repo <path>` (defaults to cwd git root, works cross-repo including external monorepos); outputs table with week label, count, marathon flag; US holiday annotation opt-in (`--holidays us`)
- [x] `pickaxe discover drift` — AHEAD/BEHIND/DIRTY/FLAGS table across a workspace (`push-needed`\|`behind`\|`uncommitted`\|`no-remote`\|`fetch-failed`); shipped v0.3.6
- [x] `pickaxe discover --submodules-only` — filters repo map to gitlink (submodule) entries only; shipped v0.3.4
- [x] `pickaxe scan` `already_extracted` annotation — flags candidates already living in a different git root (`[extracted → <remote>]`); shipped v0.3.4; does not yet skip/omit them by default (see Track A "Standalone-repo detection")
- [x] `pickaxe backup <root> --to <dest>` — bundles + working-tree snapshot of every repo in a workspace to a portable dir; `--skip-working-tree`, `--force`; shipped v0.3.5
- [x] `pickaxe restore <backup> --to <dest>` — restores repos from a pickaxe backup manifest; shipped v0.3.5
- [ ] `pickaxe discover ownership` — report the owning Git repository, nearest `.HANDOFF`, applicable instruction files, dirty state, and independent release boundary for a path before an agent edits it. Treat nested projects with their own tests, handoffs, and release cadence as extraction candidates, not automatically as submodules.
- [ ] `pickaxe diagnose handoff-drift` — compare STATE, latest session SBAR, latest handoff JSON, current diff, and declared test counts; report inconsistencies as evidence without guessing which artifact is authoritative. Initial evidence is a verified 17-vs-18 documentation inconsistency; concurrent overwrite remains an unproven hypothesis until two timestamped reads disagree.
- [ ] `pickaxe deliver handoff-rollup` — automate the STATE.md Reconciliation Algorithm defined in root `.HANDOFF/PROTOCOL.md` (archive closed session blocks to `SESSIONS/`, relocate durable reference data to the nearest owner, leave one-line pointers, re-verify the <200-line cap). Today an AI agent executes this by hand every session (confirmed 2026-07-28: no pickaxe command performed the 2026-07-24 stable-IDs housekeeping move). This is the concrete automation target — note `backup`/`restore` already write files (v0.3.5), so the gap is the reconciliation *logic*, not write-capability itself.
- [ ] `pickaxe diagnose write-conflict` MVx — implement compare-before-write fingerprints for generated handoff updates: record the source hash at read time, re-read immediately before write, and fail closed with a reconciliation report when the hash changed. Keep file leases advisory and local-only until measured conflicts justify stronger coordination.
- [ ] `pickaxe diagnose ticket-drift` — compare an Agile-Wizard ticket's checkbox/status claims against ground truth in the files it references (frontmatter fields, `lastModified`, git log) and flag divergence. Evidence: STORY `NEW-260107-AutoExec-A1S03` (created 2026-01-07) showed 0/5 acceptance criteria checked; direct inspection of the 5 referenced instruction files confirmed all 5 already had `requires:` added between 2026-01-07 and 2026-05-21 — the ticket sat stale for ~7 months while the underlying work was actually done (confirmed/corrected 2026-07-29). Same class of problem as `handoff-drift`, applied to Agile-Wizard tickets instead of STATE.md/handoff JSON. **Backlogged 2026-07-29 (user call): buildable-now per ROI table, intentionally not scoped further this session — pick up fresh, priority/evidence above still stands, no re-derivation needed.**
- [ ] `pickaxe diagnose shell-sprawl` — detect terminal/shell process count and per-shell RAM footprint using the same before/after measurement pattern already proven by the venv/dependency-tree diagnostic above (3,162MB -> 595MB after exclusion). Flag when spawned-shell count or RAM exceeds a threshold. Targets EPIC `NEW-251204-AutoExec-A1E34` Success Criterion #2 ("Shell Isolation... RAM usage <100MB per test run vs 500+MB with shell spawning") and the original terminal-spawn machine crashes (LogicWizards + Fordham) cited as the reason AutoExecBOT/Federation dev-work was pinned. **Backlogged 2026-07-29 (user call): same status as ticket-drift above — buildable-now, deliberately deferred, not analyzed further this session.**
- [x] `pickaxe diagnose instruction-bloat` — **shipped v0.4.0 (260729, A1/A3).** Programmatically applies the line-count + module-scatter triggers already hand-documented in root `copilot-instructions.md`'s own "Proactive Context Optimization" / "Modularization Triggers" section against instruction files (`AGENTS.md`, `SKILL.md`, `copilot-instructions.md`, `*.instructions.md`): flags files exceeding `--max-lines` (default 1000) and sections exceeding `--max-section-lines` (default 50). Retrofit `diagnose` with noun-dispatch (`DIAGNOSE_NOUNS`) first, mirroring `discover`'s existing pattern — 100% backward-compatible with the existing `pickaxe diagnose [path]` single-repo health check. 8 new tests (`TestDiagnoseInstructionBloat`), all green.
- [x] `pickaxe deliver instruction-rollup` — **shipped v0.4.0 (260729, A2/A4), first-ever `deliver` verb.** Given a `--from-report <findings.json>` (the `diagnose instruction-bloat --format json` output, read verbatim), extracts each flagged block to a new `<slug>.instructions.md` using the Instruction Inheritance Pattern frontmatter (`description`/`requires`/`version`/`status`/`lastModified` auto-filled; `applyTo`/`tags`/`maintainer` left as TODO placeholders), and replaces the extracted block in the source file with a one-line pointer. Dry-run by default per D-01; `--execute` to write. Idempotent — dest-exists check runs before any source mutation. 10 new tests (`TestDeliverInstructionRollup`), all green.

### ROI prioritization (2026-07-29 discovery batch)

| Candidate | Cost proxy | Efficacy proxy | Sequencing |
|---|---|---|---|
| `diagnose ticket-drift` | S — reuses `handoff-drift`'s compare-and-report shape against a new target glob | HIGH — caught 1 real stale ticket on first use today; the same grep that found it matched 230 lines across 41 Agile-Wizard files, suggesting more exist | **Backlogged 2026-07-29** — buildable now, deferred to a future session (user call, not a value judgment) |
| `diagnose shell-sprawl` | S-M — same measurement shape as the already-shipped venv/dependency-tree diagnostic | HIGH — directly targets the named, repeated real-machine-crash cause on 2 machines (LogicWizards + Fordham) | **Backlogged 2026-07-29** — buildable now, deferred to a future session (user call, not a value judgment) |
| `diagnose instruction-bloat` | S-M — rescoped 2026-07-29: reuses `copilot-instructions.md`'s own already-written trigger thresholds + exemptions verbatim, no new taxonomy | HIGH — directly targets this session's own pain (compaction churn, re-derivation cost, half-a-day burned re-establishing context) | **Shipped v0.4.0 (260729).** Full tier-aware version remains FD-18/backlogged, referenced only. |
| `deliver instruction-rollup` | S-M — rescoped 2026-07-29: reuses the already-documented Instruction Inheritance Pattern frontmatter fields, dry-run-first per D-01 | HIGH — same rationale as instruction-bloat; this is the write-side that actually stops re-teaching an agent the same context every session | **Shipped v0.4.0 (260729).** |
- [ ] `pickaxe discover split-candidates` — score directories for SIDE-PROJECT/submodule extraction using independent release cadence, scoped instructions, tests, handoff ownership, consumer count, and repeated cross-agent edit overlap. Pilot against `Intune-Deployments`; output recommendation only, never mutate repositories.
- [ ] `pickaxe deliver dirs` — clone missing repos and restore missing remotes from a canonical manifest (`repos.manifest.json`)
- [ ] `pickaxe discover drift` — compare local inventory vs canonical GitHub set, report mismatches (read-only)
- [ ] `pickaxe deliver drift` — apply fixes from drift report (dry-run by default)
- [ ] `pickaxe deliver docs` — applies baseline repo hygiene files (hook, `.editorconfig`, `.prettierrc`)
- [ ] `pickaxe document report` — writes timestamped remediation report (Markdown + JSON)

### Track C — Context oracle

- [ ] Lightbulb Log query adapter reads ai-labs anti-pattern corpus
- [ ] canonical tool inventory and provenance model is queryable
- [ ] public registry probes (Chocolatey, PSGallery, Ansible Galaxy) return actionable existence checks
- [ ] `pickaxe audit` outputs agent-agnostic handoff guidance with recommended/no-op verdict
- [ ] engagement opener template finalized for human + agent consumers

### Track D — Collaborate (git-passthrough with submodule intelligence)

The vision: `pickaxe <verb> <dotted-name>` mirrors git's collaborate surface but is submodule-aware by default. Dotted names (`tools.modules.psst`, `ai-labs`) resolve to local paths + remotes via the `.ai-labs.tools.yaml` manifest. No more manual sub → parent pointer → grandparent chains.

**Why this matters:** every LogicWizards monorepo+submodule push today requires 4-6 manual git commands across 2-3 repos, in the right order, with a STATE.md update in between. One wrong step (push parent before sub, forget to bump pointer) breaks the next agent's cold-start. `pickaxe push` eliminates the ordering problem entirely.

Command surface (mirrors `git help` collaborate section):

- [ ] `pickaxe fetch [<name>]` — query each `remote.url` for latest tag via `git ls-remote` or GH API;
write `remote.version` back to `.ai-labs.tools.yaml`; output drift table (HERE vs THERE); feeds the Locations column in the MD matrix. No writes to working tree.

### MQL — Manifest Query Language + HOBOTS Delegation Surface (design note, 260613JN)

The full vision for `pickaxe fetch` is not a fixed hardcoded command — it is the first expression of a manifest query language (MQL) where field selectors walk the YAML graph and HOBOTS personas execute the side-effecting work asynchronously and return structured data.

**Syntax:**
```
pickaxe <PERSONA> <SAK-VERB> <field-query> [as <format>]
```

**Example that prompted this design:**
```
pickaxe MATT seek *.remote.version as json
```

Breaking it down:
- `MATT` — the worker-bot persona (HOBOTS SAK: M=Matt, the task executor). Any registered persona
from `.ai-labs.tools.yaml` or the persona registry can be substituted. `SOL` = analyst, `TOTO` = watchdog/validator.
- `seek` — SAK verb (S=Seek: discovery/collection, no side effects). `ask` = query/analyze,
`knock` = act/mutate. Maps directly to the HOBOTS Seek-Ask-Knock protocol.
- `*.remote.version` — glob-style field path into the YAML manifest. `*` = all top-level nodes,
`.remote.version` = field traversal. Full XPath-like variants: `tools.*.status`, `**.tags`, `**.remote[public=true].url`.
- `as json` — output format: `json` | `table` | `yaml` | `md`. Default: `table`.

**What MATT does on `seek *.remote.version`:**
1. Parse manifest — extract all nodes where `remote.url` is not `~`
2. For each: `git ls-remote --tags <url>` → latest semver tag → that is THERE
3. Derive HERE from `applyTo` path → `git -C <path> describe --tags --abbrev=0`
4. Return JSON: `{ "ai-labs": { "here": "0.1.0", "there": "0.1.3" }, "pickaxe": { ... } }`
5. Pickaxe receives the JSON, writes `remote.version:` into YAML, regenerates MD

**Why this matters (agent-to-agent pattern):** MATT executes the blocking network calls; pickaxe stays non-blocking. The `as json` contract is the handoff format — AJAX-style: MATT goes away, returns structured data, pickaxe applies it. Any AI agent running `pickaxe MATT seek ... as json` gets a self-updating manifest without needing to know git ls-remote syntax or GitHub API endpoints.

**MQL field selector rules (draft):**
- `*` — all direct PROJECT nodes
- `**` — all nodes (PROJECT + SUB, any depth)
- `<name>` — exact dotted path (`tools.modules.psst`)
- `<glob>` — wildcard segment (`tools.*.status`, `**.remote.url`)
- `[<key>=<value>]` — filter predicate (`**.remote[public=true].url`)
- `.` — field accessor on current node

**Planned MQL queries (examples to drive spec):**
```
pickaxe MATT seek **.remote[public=true].url as json   # all public remotes
pickaxe SOL  ask  **.status as table                   # all statuses, analyst summary
pickaxe TOTO seek **.version as json                   # all HERE versions for drift check
pickaxe MATT seek tools.*.related.siblings as yaml     # a2m8 sibling graph
```

**Milestone:** v0.8 — first MQL query (`*.remote.version`) must round-trip: seek → json → YAML write → MD regenerate → drift visible in Locations column.
- [ ] `pickaxe pull <name>` — pull the named submodule; update parent pointer commit; surface what
landed (auto-runs the AGENTS.md 5-step read-order: STATE.md, latest handoff JSON, git log, AGENTS.md, then stops). Enforces the "PULL BEFORE PUSH" hard gate from AGENTS.md.
- [ ] `pickaxe push <name>` — the crown jewel. Knows the full chain:
  - **who** — `remote.url` from manifest
  - **what** — `git status` in the sub (refuses to push with dirty tree unless `--force`)
  - **where** — parent(s) referencing this sub (discovered via workspace model from v0.4)
  - **when** — writes timestamp to sub's STATE.md before pushing
  - **how** — sequence: update STATE.md → stage (`git add -A`) → commit (COMMIT-MSG template) →
    push sub → bump parent pointer → push parent(s) → optionally recurse to grandparent
  - Dry-run by default; `--execute` to run. `--no-parent` skips pointer bump.
- [ ] `pickaxe status [<name>]` — cross-repo drift summary: version skew, uncommitted changes,
unpushed commits, pointer out of sync. One-liner per tool, color-coded.
- [ ] `pickaxe log <name>` — `git log` for a tool by dotted name; no path-hunting required.
- [ ] `pickaxe <verb> <name>` passthrough — any unrecognized verb is forwarded:
`git -C <path-from-manifest> <verb>`. Makes all `git` muscle memory work on tool names.

Foundational dependencies:
- `.ai-labs.tools.yaml` `remote.url` field — done (v0.2 schema)
- `.ai-labs.tools.yaml` `remote.version` field — needed; add as `~` seed for all 17 entries
- Workspace parent-chain model — needed (v0.4)

### Track E — Manifest management + workspace sync

The YAML is the source of truth. Markdown indexes and active-context files are generated projections and never write back to YAML. `.AI-TRAINING/` artifacts route to the nearest owning repository or subtree; the workspace root is reserved for genuinely workspace-global material. The normative implementation contract is [`.HANDOFF/AI-TRAINING-MANIFEST.md`](.HANDOFF/AI-TRAINING-MANIFEST.md).

**`pickaxe discover tools`** — YAML → MD manifest generation:

- [ ] `pickaxe discover tools [--write]` — read `.ai-labs.tools.yaml`, emit `.ai-labs.tools.md` companion (Locations/Actions matrix, hex status colors, HERE/THERE drift column)
- [ ] `pickaxe discover tools --diff` — show delta between current YAML and on-disk MD; non-zero exit if drift detected (CI-safe)
- [ ] `pickaxe discover tools --sync` — regenerate projections from YAML and report manual projection drift; never back-propagate Markdown edits
- [ ] `pickaxe discover tools --graph` — emit DOT/mermaid from `related:` edges for visualization

**`.AI-TRAINING/` owner-local fork** — any peer node can fork the tools manifest at its nearest ownership boundary, override HERE paths and implemented tool subset, and detect upstream drift:

- [ ] `.AI-TRAINING/tools.yaml` — owner-local fork seeded from `ai-labs/.ai-labs.tools.yaml`; HERE fields remapped to local paths; unused tools use an explicit lifecycle state
- [ ] `.AI-TRAINING/.sync-ref` — tracks last-synced ai-labs SHA, content hashes, and node identity; written by `pickaxe sync`
- [ ] `pickaxe sync [ai-labs]` — compare UUID plus content hash and lineage; emit `DELTA.md` for upstream changes and local overrides; update `.sync-ref`
- [ ] `pickaxe context resolve` — apply nearest-owner precedence and lifecycle filters, then generate a bounded active-context view
- [ ] `pickaxe training classify|promote|archive` — transition manifest lifecycle explicitly; T4/T5 promotion requires sanitization and user approval
- [ ] `pickaxe discover tools --here <path>` — generate MD with HERE remapped to `<path>` (supports fork init from upstream YAML without manual edits)

Foundational dependency: `.ai-labs.tools.yaml` `applyTo` paths must be absolute or resolvable from workspace root for HERE detection to work across machines.

---

### Done criteria by milestone

- [ ] `Track A` done (mis-numbered `v0.2` in the original plan — see Version plan reconciliation note): extraction pipeline runs end-to-end on at least one real carve-out
- [x] `v0.4` done: hygiene + drift commands catch and remediate missing repo/remote state (`discover`/`diagnose`/`discover drift` ✅ shipped v0.2.0–v0.3.6; `diagnose instruction-bloat`/`deliver instruction-rollup` ✅ shipped v0.4.0; `deliver dirs`/`deliver drift` remediation still ❌)
- [ ] `v0.6` done: `pickaxe push <name>` completes sub → parent chain without manual git steps
- [ ] `v0.8` done: `pickaxe fetch` populates `remote.version` and drift table is live
- [ ] `v0.9` done: `pickaxe discover tools` generates deterministic Markdown from YAML, `pickaxe context resolve` excludes inactive evidence, and `pickaxe sync` emits `DELTA.md`
- [ ] `v1.0` done: context-oracle flow can answer "do I need to build this?" with provenance-backed evidence

---

## Version plan

### Shipped (ground truth, verified 2026-07-29 — 119/119 tests green)

| Version | Date | Theme | Key features |
|---|---|---|---|
| v0.1.0 | 260506 | Discovery | `scan` — tool-worthiness scoring, `--output` Markdown report, `--dry-run` |
| v0.2.0 | 260612 | Repo health (Track B) | `discover`, `diagnose` — 5D command surface, repo map + health flags |
| v0.3.2 | 260603 | Gitlink fix (Track B) | submodule worktree (`.git`-as-file) support in `discover`/`diagnose` |
| v0.3.3 | 260615 | Commit cadence (Track B) | `discover commit-trends`, `--format json` on scan/discover |
| v0.3.4 | 260615 | Extraction annotation (Track B) | `scan` `already_extracted` field, `discover --submodules-only` |
| v0.3.5 | — | Backup/restore (Track B) | `backup`, `restore` — full workspace snapshot + recovery |
| v0.3.6 | — | Remote drift (Track B) | `discover drift` — ahead/behind/dirty/flags table |
| v0.4.0 | 260729 | Instruction hygiene (Track B) | `diagnose` noun-dispatch retrofit (A1); first-ever `deliver` verb (A2); `diagnose instruction-bloat` (A3); `deliver instruction-rollup` (A4) |
| v0.4.1 | 260729 | Bugfix (Track B) | Fixed LB-03: `deliver instruction-rollup` silently dropped every extraction after the first when a whole-file finding overlapped section findings. Snapshot-before-mutate + `skipped_overlap` status; caught via sandbox test before it ever touched a live file. |
| v0.4.2 *(current)* | 260729 | Bugfix (Track B) | Fixed LB-04: `.github/` sources extracted to `.github/` directly, which VS Code never auto-discovers. Now routes to `.github/instructions/`; pointer links resolve relative to the source file's own directory. Dogfood-validated 260730 against root repo's live `copilot-instructions.md` via `diagnose instruction-bloat`. |

### Planned (theme slots — not yet sequenced chronologically, see reconciliation note)

| Version | Theme | Key features |
|---|---|---|
| TBD (Track A) | Extraction | `--execute`, subdir mode, `.pickaxe/` chain-of-custody, AI context detection, full pipeline dry-run output — **unscheduled**, see note below |
| TBD (Track A) | Clustering | Cluster detection, shared-history grouping — **unscheduled**, see note below |
| v0.4 | Workspace | `pickaxe init <slug>`, `pickaxe workspace init`, `pickaxe workspace split` — cascade-aware scaffold for HOBOTS `.PROTOCOL/` + `AGENTS.md` + `DESIGN.md` + `SPEC.md` inheritance; nested monorepo support; `SPLIT-FROM:`/`SPLIT-TO:` lineage in STATE.md |
| v0.5 | Automation | `--since`, GitHub Actions workflow (`--format json` already shipped early, v0.3.3 — see Shipped table) |
| v0.6 | Collaborate | `pickaxe push/pull/fetch/status <dotted-name>` — submodule-aware git passthrough; full sub → parent chain in one command; `remote.version` drift table |
| v0.7 | Collaborate+ | `pickaxe log/diff/<verb>` passthrough; `--wrap` flag writes handoff + STATE.md before push; multi-parent chain (sub → mono → grandparent) |
| v0.8 | MQL + Fetch | `pickaxe MATT seek *.remote.version as json` — first MQL round-trip; HOBOTS persona delegation surface; `remote.version` written back to YAML; drift column live in tools.md |
| v0.9 | Manifest | `pickaxe discover tools` (YAML → MD round-trip); `pickaxe sync` (`.AI-TRAINING/` fork + delta); `pickaxe discover tools --diff` (CI drift gate) |
| v1.0 | Catalog | Multi-repo index, persistent state, query interface |

> **Reconciliation note (2026-07-29):** the original plan slotted Extraction at v0.2 and Clustering at v0.3. Actual development took a different path — six versions (v0.2.0 → v0.3.6) shipped entirely under Track B (repo hygiene/drift), and Track A (extraction) has never shipped anything. Those two version numbers are now taken by unrelated work, so Extraction/Clustering have no reserved slot. **Flagged for a decision, not resolved here:** either wedge Track A in before Workspace (shifting v0.4→v0.9 down by one each) or leave Track A unscheduled/opportunistic. Not changed unilaterally in this pass — doing so would cascade into every Track D/E cross-reference to these same numbers elsewhere in this file (`v0.4` workspace parent-chain dependency, `v0.8` MQL milestone, `v0.9` Track E foundational dependency).
>
> **Versioning is approximate, not a contract (2026-07-29):** the same collision recurred the day this note was written — `diagnose instruction-bloat`/`deliver instruction-rollup` (A1-A4) shipped as "v0.4.0" because it was simply the next integer after v0.3.6, but thematically it is Track B (repo/instruction hygiene), not the Track "Workspace" theme this plan had already reserved v0.4 for. Not renamed to v0.3.7 retroactively — the commit is already pushed, and chasing a clean number after the fact costs more than it's worth. This is expected under an agile cadence: theme-slot version *plans* are a forecast, not a lock; shipped version *numbers* are assigned in shipping order, not theme order. When they disagree, trust the Shipped table (ground-truthed against `git log` + tests) over the Planned table, and fix forward with a note like this one rather than rewriting history.

**v0.4 design reference:** `wwwizards/ai-labs` `.HANDOFF/DESIGN.md` D-10, `.HANDOFF/FEATURE.md` F-pickaxe-workspace, `.PROTOCOL/README.md` § Inheritance Scope.

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
| v0.7 | Collaborate | `pickaxe push/pull/fetch` — submodule-aware git passthrough |
| v1.0 | Context oracle | `pickaxe audit` — full engagement-opener report |

---

*Roadmap authored 26-0518. North Star added 26-0526. Track D (Collaborate/MQL) added 26-0613. Track E (Manifest/Workspace Sync) added 260714. Historical reference session: `HANDOFF.interrim-260518JN-Miners.md` (artifact no longer present in the workspace).*
