# Design: PICKAXE

> **Portable Independent Collaborative-Knowledge AjaX-Extender**

```
# --------------------------------------------------------------------------
# NOTES:    DESIGN.md
# --------------------------------------------------------------------------
# ABSTRACT: Architectural decisions for the PICKAXE CLI. Records the
#     rationale for key design choices — what we decided, why, and what
#     alternatives were rejected. Read before implementing new features.
#     Acronym locked 2026-06-16. Release target: 2026-07-04 (Independence Day).
# CREATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# UPDATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - A1-A4 shipped, 119 tests green
# UPDATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - LB-03 fix, 121 tests green
# UPDATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - LB-04 fix, 123 tests green
# ARCHITECT: SOLOMON
# TECHLEAD:  JN (Joe Negron -- LogicWizards.NYC)
# VERSION:  0.4.2  (mirrors the pickaxe CLI version; ../ROADMAP.md is
#           canonical. All .HANDOFF docs bump together at every wrap.)
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

## Command model — 5D surface (design target, not yet implemented as of v0.3.6)

Commands follow the 5D methodology (Discover → Diagnose → Design → Deliver → Document). Every phase is a top-level subcommand; the noun after it is the target artifact or operation. Discover and Deliver share nouns intentionally — the same noun read-only in Discover, mutating in Deliver. This makes dry-run discipline structural, not optional.

*Status: aspirational. The shipped v0.3.6 CLI is `discover [commit-trends|drift]`, `diagnose`, `scan`, `backup`, `restore` — a flatter surface that does not follow this noun model. See the Reconciliation note after D-13 and `../ROADMAP.md` Track A.*

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

`pickaxe doctor` → `pickaxe diagnose` `pickaxe inventory` → `pickaxe discover` `pickaxe hydrate` → `pickaxe deliver dirs` (or `deliver drift`) `pickaxe drift` → `pickaxe discover drift` (read) + `pickaxe deliver drift` (fix) `pickaxe provision` → `pickaxe deliver docs` `pickaxe report` → `pickaxe document report`

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

---

## D-08: `pickaxe workspace split` is the peer-node bootstrapping primitive (260612)

`federation/F5` (Federated Peer Nodes) needs a mechanism for creating a peer node from an existing workspace subtree. `workspace split` with `SPLIT-FROM:`/`SPLIT-TO:` lineage (D-06) is exactly that primitive. A subtree becomes a peer node by splitting out, receiving its own Layer-2 scaffold via `workspace init`, and gaining its own `.AI-TRAINING/` loop.

**Cross-reference:** `wwwizards/ai-labs` `federation/FEATURES/F5-federated-peer-nodes.md`.

**Ticket dependency (2026-07-29):** [NEW-260528-IntuneDeployments-C1S03-STORY-ART-Repo-Split-Pre-Scaffold](../../../Agile-Wizard/DATA/Phoenix-CPAs/BACKLOG/NEW-260528-IntuneDeployments-C1S03-STORY-ART-Repo-Split-Pre-Scaffold.md) assumes a `repos.manifest.json` entry plus a `pickaxe deliver` command for manifest-driven clone post-split — neither exists yet. `workspace split`/`workspace init` (this decision) and `deliver` (Command model above) are both still design-target only; the STORY's acceptance criteria cannot be checked against real tooling until this D-08 primitive ships.

---

## D-09: Layer numbering aligns with federation/F2 (260612)

Federation FEATURE.md defines: L0=ai-labs SoT, L1=published defaults, L2=workspace root, L3..N=per-dir overrides. `pickaxe workspace init` operates at **L2** (workspace root scaffold), not L0. Prior references to "Layer 0" in pickaxe context meant L2 in federation terms. Use federation numbering going forward to avoid confusion when docs are read together.

---

## D-10: F2 inheritance conflict resolution — tree-depth wins, `--force` to override (260612)

`federation/F2` open design question: when two `requires:` parents disagree, last-wins by tree depth or explicit priority? Answer: **tree depth wins** (child overrides parent), and `--force` is required to overwrite any customized anchor file. This is consistent with nested `.git/config` semantics and with `workspace init`'s existing "never silently clobber" behavior. Closes the F2 open question.

---

## D-11: `check-headers.py` is the F4 pre-gate candidate; it already exists (260612)

`federation/F4` (Knowledge Classification) needs an artifact-level enforcement gate. `wwwizards/ai-labs/experiments/autodocs/check-headers.py` v0.4.260611 is the prototype — all flags tested green. Wire it as a pre-commit hook in pickaxe to satisfy `F-pickaxe-workspace` acceptance criteria item 6 ("all generated files pass the validator on first run"). The `pyst autodoc headers` integration (MVx-260611) is a future upgrade, not a blocker.

---

## D-12: T0 emit on every workspace init/split (260612)

Every `pickaxe workspace init` and `pickaxe workspace split` invocation must write a structured record into the nearest owning workspace's `.AI-TRAINING/` directory under the F6 dotted namespace. This makes every scaffold/split a traceable provenance event — consistent with D-07 (session log as training data) and D-06 (lineage in STATE.md). The F6 namespace format: `LIGHTBULB-LOG.<stratum>.<org>.<project>.<target>.<verb>.md`.

---

## D-13: Active context and historical evidence are separate planes (260725)

[`AI-TRAINING-MANIFEST.md`](AI-TRAINING-MANIFEST.md) is the canonical pickaxe implementation contract for nearest-owner routing, UUID-plus-content-hash identity, lifecycle states, deterministic precedence, and generated active-context views. YAML is authoritative; Markdown is a generated projection. Normal ingestion loads only resolved active/default entries. Archived, quarantined, retracted, candidate, and evidence entries remain queryable but never enter default context merely because they still exist on disk.

Git preserves retired content history. A retained evidence artifact must be represented as evidence or archive state, not as an obsolete full decision with a supersession banner in the active plane.

---

## Reconciliation note (2026-07-29)

This file previously repeated the entire "Architecture sketch" + "Command model" block twice (once above D-01, once again after D-13, the second copy with inconsistent heading levels) — an editing artifact, not intentional structure. The duplicate has been removed; the single canonical copy above D-01 remains authoritative.

Separately, and more substantively: the "Command model — 5D surface" section above describes a `discover/diagnose/design/deliver/document` noun-based CLI that **was never built**. The CLI that actually shipped (v0.1.0 → v0.3.6, see `../ROADMAP.md` AS-IS section) took a simpler, flatter path: `discover [commit-trends|drift]`, `diagnose`, `scan`, `backup`, `restore`. Only `discover` and `diagnose` exist as real top-level verbs from the 5D model; `design`, `deliver`, and `document` do not exist at all, and `scan`/`backup`/`restore` aren't accounted for by the 5D model in any form. The Command model section is left in place as the Track A/D/E design target (see ROADMAP.md's Track A reconciliation), not a description of current behavior — treat every code block under it as aspirational until ROADMAP.md marks the corresponding item `[x]`.
