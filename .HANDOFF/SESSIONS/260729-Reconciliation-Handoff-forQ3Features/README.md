# PICKAXE - Reconciliation Handoff for Q3 Features

```
# --------------------------------------------------------------------------
# HANDOFF: 260729-Reconciliation-Handoff-forQ3Features/README.md
# --------------------------------------------------------------------------
# ABSTRACT: Contains thumbprint, preferred terminal (PICKAXE), doc read-order, 
#   quickstart orientation, near-term goals (A1→A4 in strict order + the 3 open 
#   decisions to answer first), long-term/backlog goals (Track B/C + 
#   Federation context contract), and the version-alignment rule going forwar
#
#   This doc was meant to be initiated by a /prompt but failed. it records 
#   most of the rationale for key design choices — what we decided, why & what
#   alternatives were rejected. Read before implementing new features.
#   Acronym locked 2026-06-16. Released: 2026-07-04 (Independence Day
#
#   The handoff is designed to make a fresh session cheap, not expensive: 
#   STATE.md now has the exact next steps (A1→A4) and features-listing.md 
#   has the open decisions that must be answered first. A new session's mandated 
#   read-order (STATE.md → git log → copilot-instructions.md → source) will 
#   pick this up in seconds, not "more training" — that's the whole point of 
#   writing it down instead of carrying it in conversational memory.
#
# CREATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON
# UPDATED:  260729 BY: Joe Negron   
# ARCHITECT: JN (Joe Negron -- LogicWizards.NYC)
# TECHLEAD:  JN (Joe Negron -- LogicWizards.NYC)
# VERSION:  0.3.6 --> 0.4.0
# STAGE:    ACTIVE-HANDOFF-PROMPT
# --------------------------------------------------------------------------
```

You are picking up a fully-planned, doc-reconciled MVP. Do not re-derive scope —
read the docs below first, in this order, then start coding.

## Thumbprint

Use `Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON` in every `UPDATED:` (and
`CREATED:`/`ARCHITECT:`/`TECHLEAD:` where you're the first author) header field
you touch in this repo. If the model/host changes, state the new thumbprint and
ask before swapping — don't silently keep or silently change it.

## Preferred terminal

Use `ai_labs_run(terminal: "PICKAXE", command: "...")` for all pytest/git work
scoped to this repo. Never `run_in_terminal` (spawns a fresh shell, reloads the
full profile). If the PICKAXE terminal isn't open, ask the user to open it
before running anything — don't spawn a substitute.

## Location of docs (read in this order)

Repo root: `SOLUTIONS/DevOps/SIDE-PROJECTS/pickaxe/` (git submodule, remote
`wwwizards/pickaxe`, branch `main`).

1. `.HANDOFF/STATE.md` — current state, "Interim handoff (2026-07-29)" section
   has the exact next steps.
2. `.HANDOFF/features-listing.md` — checkbox tracker, Franklin priorities
   (A1-A4 current sprint), and the "Decisions still needed" section — answer
   those three open questions before writing code.
3. `.HANDOFF/features-map.md` — mermaid visual (same data as #2, diagram form).
4. `ROADMAP.md` — AS-IS/TO-BE narrative, canonical version record.
5. `.HANDOFF/DESIGN.md` — architecture rationale, read before any new design
   decision.
6. `.HANDOFF/FEATURE.md` — feature intent/scope, F-03 section covers this MVP.
7. `pickaxe.py` / `test_pickaxe.py` — source ground truth. `discover`'s
   `DISCOVER_NOUNS` + `_cmd_discover` noun-dispatch pattern (~line 657, 1068)
   is the pattern to mirror for `diagnose`. `deliver` does not exist yet.

## Quickstart orientation

- Shipped CLI: v0.3.6, 98 tests green (`discover` incl. `commit-trends`/`drift`,
  `diagnose`, `scan`, `backup`, `restore`). No noun-dispatch on `diagnose` yet.
  No `deliver` subparser exists at all.
- This session's job: build the diagnose→deliver MVP for instruction-bloat
  detection + instruction-rollup extraction, per the A1-A4 spec below.
- Test convention: `tmp_path` pytest fixtures + real `git init`/`git commit` via
  `subprocess.run` (see `test_pickaxe.py` `TestDiscover`/`TestDiagnose` classes).
  Both direct function calls and CLI-level `subprocess.run(['python',
  'pickaxe.py', ...])` tests are used — follow existing patterns, don't invent
  a new fixture style.
- TDD guardrail (repo-wide, non-negotiable): test-first, one change per test
  run, never claim "fixed" without a green test run.

## Near-term goals (this sprint, Franklin A-tier, in strict order)

1. **A1** — retrofit `diagnose` with noun-dispatch (`DIAGNOSE_NOUNS` set +
   `noun` arg), mirroring `discover`'s existing pattern exactly.
2. **A2** — add the first-ever top-level `deliver` subparser + `_cmd_deliver`
   dispatch function.
3. **A3** — `diagnose instruction-bloat` (blocked on A1): file-count/whole-file
   line-threshold check, section/heading line-count parser for the >50-line
   scattered-pattern rule, `--format table|json` + `--save` convention.
4. **A4** — `deliver instruction-rollup` (blocked on A2 + A3's output schema):
   diagnose→deliver JSON handoff contract (`file`/`start_line`/`end_line`/
   `reason`), frontmatter auto-fill rules, dry-run-by-default + `--execute`,
   idempotent pointer check (skip if already extracted).
5. Write `tmp_path`-based tests for both new commands (new synthetic-
   instructions fixtures), following existing `TestDiscover`/`TestDiagnose`
   conventions.

**Before A3/A4 can start, answer these three open decisions** (in
`features-listing.md` § "Decisions still needed" — don't re-derive, decide and
record there):
- Scan scope for `diagnose instruction-bloat`: single-repo (cwd) or
  workspace-wide (like `scan`/`backup`)?
- Handoff format between A3 and A4: `--from-report findings.json` vs. manual
  `--file/--start/--end` flags?
- Default line-count threshold: hardcoded 1000, or a `--max-lines` flag?
  Default for the per-section (>50-line) rule?

## Long-term goals (Track B/C backlog — reference only, not this sprint)

- Track B (real, deliberately deferred): `discover ownership`,
  `discover split-candidates`, `diagnose handoff-drift`, `diagnose
  write-conflict`, venv/dependency-tree exclusion detection, `deliver
  handoff-rollup`, `deliver dirs`, `deliver drift`, `deliver docs`.
- Track C (backlogged 2026-07-29, user call — do not re-open unless asked):
  `diagnose ticket-drift`, `diagnose shell-sprawl`, `scan` standalone-repo
  skip-by-default.
- Extraction pipeline (`--execute` mode, `.pickaxe/` chain-of-custody,
  AI-context detection, cluster detection) — 0% built, largest unbuilt
  surface, out of scope for this sprint.
- Workspace init/split (F-02, v0.4 target): `pickaxe init <slug>`, `pickaxe
  workspace init`, `pickaxe workspace split <sub-path>` — undefined at the
  implementation level, not prioritized.
- Federation context contract (`pickaxe context discover|route|resolve|check|
  promote`) — design-only per `AI-TRAINING-MANIFEST.md`, pinned until the
  Wizard explicitly names the first MVx. Not related to this sprint's work.

## Version number for all docs moving forward

**0.3.6** — every `.HANDOFF/*.md` doc plus `ROADMAP.md` now mirrors the CLI's
shipped version as a single number (no more independent per-doc revision
counters — that caused a "3-version-ambiguity" bug fixed twice in one day on
2026-07-29). `ROADMAP.md` is the canonical source. **When you ship the next
CLI change (A1-A4), bump ALL of these files' `VERSION:` header field to the
new number together, in the same commit** — do not let them drift apart again.

## Commit discipline

Submodule remote is `wwwizards/pickaxe` — commit here first, then (separately,
only if asked) bump the parent LogicWizards monorepo's submodule pointer. Use
`git commit -F <file>` for multi-paragraph bodies (never chained `-m "..." -m
"..."`). Fetch + check divergence before any push; ask before pushing.
