# Design: pickaxe

```
# --------------------------------------------------------------------------
# NOTES:    DESIGN.md
# --------------------------------------------------------------------------
# ABSTRACT: Architectural decisions for the pickaxe CLI. Records the
#     rationale for key design choices — what we decided, why, and what
#     alternatives were rejected. Read before implementing new features.
# CREATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# UPDATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# VERSION:  0.2.0
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```

------------------------------

## Architecture sketch

### Layer 1: Discovery

- filesystem walk
- script header parsing
- git metadata collection

### Layer 2: Repo health

- detect repo roots and nested boundaries
- inspect `.git/config` for remotes
- emit health flags (`missing_git`, `missing_origin`, `remote_mismatch`, `detached_folder`)

### Layer 3: Remediation

- `hydrate` from canonical manifest
- optional remote restore
- non-destructive mode as default

### Layer 4: Context

- ai-labs Lightbulb Log lookup
- canonical tool inventory lookup
- public registry existence probes

------------------------------

## Command model — 5D surface (v0.2 target)

Commands follow the 5D methodology (Discover → Diagnose → Design → Deliver → Document). Every phase is a top-level subcommand; the noun after it is the target artifact or operation. Discover and Deliver share nouns intentionally — the same noun read-only in Discover, mutating in Deliver. This makes dry-run discipline structural, not optional.

```
pickaxe discover [drift|dirs|docs|*]     # AS-IS state: read-only scan & map
pickaxe diagnose [git|remote|config|*]   # root-cause: where does it hurt?
pickaxe design   [library|script|app|test|solution|experiment|plan|play|playbook|runbook]
pickaxe deliver  [drift|dirs|docs|*]     # execute treatment (dry-run by default)
pickaxe document [session|handoff|report|runbook]
```

### Phase → operation mapping

| Phase | What it does | Mutates? |
|---|---|---|
| `discover` | walk repos, emit AS-IS map (paths, remotes, branches, health flags) | no |
| `diagnose` | inspect `.git/config`, detect missing git, missing origin, stripped config, remote mismatch | no |
| `design` | scaffold a new artifact from a template (library, script, app, test, etc.) | yes — creates files |
| `deliver` | execute the plan from diagnose/discover: fix drift, hydrate dirs, provision docs | yes — dry-run first |
| `document` | generate handoff artifacts, session records, runbooks, autodoc stubs | yes — creates files |

### Subcommand nouns (initial set)

**discover / deliver targets:**
- `drift` — compare local inventory vs canonical manifest, report mismatches
- `dirs` — directory structure map or repair
- `docs` — find or generate documentation stubs
- `*` (default) — full scan across all targets

**diagnose targets:**
- `git` — verify `.git/` exists and is a valid repo root
- `remote` — verify `origin` is present and reachable
- `config` — inspect `.git/config` for stripped or malformed stanzas
- `*` (default) — run all checks

**design templates:**
- `library` — Python/PS module scaffold
- `script` — standalone script with header template
- `app` — application scaffold (CLI entrypoint + tests)
- `test` — test file stub (pytest / Pester)
- `solution` — full solution folder (script + test + README + .HANDOFF/)
- `mvx` — mini-viability experiment scaffold (hypothesis + test + observation)
- `plan` — plan document stub
- `play` / `playbook` / `runbook` — ops procedure document stubs

**document targets:**
- `session` — generate session record from git log delta
- `handoff` — generate/update STATE.md from current session context
- `report` — timestamped Markdown + JSON remediation report
- `runbook` — ops procedure document

### Prior command names (superseded)

`pickaxe doctor` → `pickaxe diagnose`
`pickaxe inventory` → `pickaxe discover`
`pickaxe hydrate` → `pickaxe deliver dirs` (or `deliver drift`)
`pickaxe drift` → `pickaxe discover drift` (read) + `pickaxe deliver drift` (fix)
`pickaxe provision` → `pickaxe deliver docs`
`pickaxe report` → `pickaxe document report`

### Design guardrails

- dry-run first for all mutating operations (`deliver`, `design`, `document`)
- no forced overwrite of existing directories
- all remediation actions logged with timestamp + rationale
- keep output agent-agnostic (human-readable + machine-readable)
- `discover` and `diagnose` are always read-only — no exceptions

------------------------------

## D-01: Discovery-only by default; execution is opt-in

pickaxe never modifies a repo without `--execute`. All destructive operations (git-filter-repo, repo creation, push) require explicit opt-in. Default behavior is always a dry-run report.

**Rationale:** git-filter-repo rewrites history. A single wrong path glob can corrupt the source repo. Trust must be earned through readable dry-run output before any execution is allowed.

---

## D-02: stdlib only for core; optional deps for execution mode

v0.1 core: Python stdlib only. No `pip install`. Runs on any machine with Python 3.8+.

v0.2+ execution mode adds `git-filter-repo` and `gh` as runtime requirements, installed via `--install-deps` (platform-aware: brew / pip / choco).

**Rationale:** The discovery value is immediate. Installation friction must not block the first useful run.

---

## D-03: `.pickaxe/` chain-of-custody lives in both source and destination

Every extraction writes an audit trail on both ends — `extractions.md` in the source, `provenance.md` + `filter-repo.cmd` in the destination. Extractions are reversible to audit without hunting git blame.

---

## D-04: AI context files travel with extractions

When extracting a subdir, pickaxe detects and carries ancestor AI instruction files (`AGENTS.md`, `copilot-instructions.md`, `HANDOFF*.md`) into `.pickaxe/ai-instructions.md` at the destination. Context is not lost at extraction boundaries.

---

## D-05: Workspace scaffold uses HOBOTS cascade model

The v0.4 workspace commands (`init`, `workspace init`, `workspace split`) implement the HOBOTS cascade-inheritance model defined in `wwwizards/ai-labs`:

- Four anchor file types cascade root-to-leaf: `.PROTOCOL/README.md`, `AGENTS.md`, `DESIGN.md`, `SPEC.md`
- Leaf wins on conflict; absence = inherit from nearest ancestor
- pickaxe is cascade-aware: reads existing layers before scaffolding; only writes the delta
- `--force` required to overwrite any existing anchor file

**Specification:** `wwwizards/ai-labs` `.PROTOCOL/README.md` § Inheritance Scope, `.HANDOFF/DESIGN.md` D-08 + D-10

---

## D-06: Lineage is tracked in STATE.md on workspace split

`pickaxe workspace split <sub-path>` writes:
- `SPLIT-TO: <destination-repo-url>` in the source STATE.md
- `SPLIT-FROM: <source-repo-url>/<original-path>` in the destination STATE.md

This creates a permanent lineage chain that survives repo renaming and makes the origin of any extracted workspace discoverable without git blame archaeology.

---

## D-07: Session log instrumentation is a design-in-from-the-start requirement

Every CLI invocation should optionally emit a structured session event to `.pickaxe/SESSIONS/` (phase, target, result, flags, timestamp). This feeds the `260527-pickaxe-session-logs-as-training-data.md` pattern: session logs across repos become labeled trajectory data for the AIM / xSME model without any additional annotation effort.

**Do not bolt this on later.** The log schema must be designed before v0.2 execution mode ships.


### Layer 1: Discovery

- filesystem walk
- script header parsing
- git metadata collection

### Layer 2: Repo health

- detect repo roots and nested boundaries
- inspect `.git/config` for remotes
- emit health flags (`missing_git`, `missing_origin`, `remote_mismatch`, `detached_folder`)

### Layer 3: Remediation

- `hydrate` from canonical manifest
- optional remote restore
- non-destructive mode as default

### Layer 4: Context

- ai-labs Lightbulb Log lookup
- canonical tool inventory lookup
- public registry existence probes

## Command model — 5D surface (v0.2 target)

Commands follow the 5D methodology (Discover → Diagnose → Design → Deliver → Document). Every phase is a top-level subcommand; the noun after it is the target artifact or operation. Discover and Deliver share nouns intentionally — the same noun read-only in Discover, mutating in Deliver. This makes dry-run discipline structural, not optional.

```
pickaxe discover [drift|dirs|docs|*]     # AS-IS state: read-only scan & map
pickaxe diagnose [git|remote|config|*]   # root-cause: where does it hurt?
pickaxe design   [library|script|app|test|solution|experiment|plan|play|playbook|runbook]
pickaxe deliver  [drift|dirs|docs|*]     # execute treatment (dry-run by default)
pickaxe document [session|handoff|report|runbook]
```

### Phase → operation mapping

| Phase | What it does | Mutates? |
|---|---|---|
| `discover` | walk repos, emit AS-IS map (paths, remotes, branches, health flags) | no |
| `diagnose` | inspect `.git/config`, detect missing git, missing origin, stripped config, remote mismatch | no |
| `design` | scaffold a new artifact from a template (library, script, app, test, etc.) | yes — creates files |
| `deliver` | execute the plan from diagnose/discover: fix drift, hydrate dirs, provision docs | yes — dry-run first |
| `document` | generate handoff artifacts, session records, runbooks, autodoc stubs | yes — creates files |

### Subcommand nouns (initial set)

**discover / deliver targets:**
- `drift` — compare local inventory vs canonical manifest, report mismatches
- `dirs` — directory structure map or repair
- `docs` — find or generate documentation stubs
- `*` (default) — full scan across all targets

**diagnose targets:**
- `git` — verify `.git/` exists and is a valid repo root
- `remote` — verify `origin` is present and reachable
- `config` — inspect `.git/config` for stripped or malformed stanzas
- `*` (default) — run all checks

**design templates:**
- `library` — Python/PS module scaffold
- `script` — standalone script with header template
- `app` — application scaffold (CLI entrypoint + tests)
- `test` — test file stub (pytest / Pester)
- `solution` — full solution folder (script + test + README + .HANDOFF/)
- `mvx` — mini-viability experiments' scaffold (hypothesis + test + observation - to fail forward fast)
- `plan` — plan document stub
- `play` / `playbook` / `runbook` — ops procedure document stubs

**document targets:**
- `session` — generate session record from git log delta
- `handoff` — generate/update STATE.md from current session context
- `report` — timestamped Markdown + JSON remediation report
- `runbook` — ops procedure document

## Prior command names (superseded)

`pickaxe doctor` → `pickaxe diagnose`
`pickaxe inventory` → `pickaxe discover`
`pickaxe hydrate` → `pickaxe deliver dirs` (or `deliver drift`)
`pickaxe drift` → `pickaxe discover drift` (read) + `pickaxe deliver drift` (fix)
`pickaxe provision` → `pickaxe deliver docs`
`pickaxe report` → `pickaxe document report`

## Design guardrails

- dry-run first for all mutating operations (`deliver`, `design`, `document`)
- no forced overwrite of existing directories
- all remediation actions logged with timestamp + rationale
- keep output agent-agnostic (human-readable + machine-readable)
- `discover` and `diagnose` are always read-only — no exceptions