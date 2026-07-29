# Feature: pickaxe

```
# --------------------------------------------------------------------------
# NOTES:    FEATURE.md
# --------------------------------------------------------------------------
# ABSTRACT: Feature intent and scope for the pickaxe CLI tool. Pickaxe
#     mines tool-worthy scripts from compound mono-repos and extracts them
#     to standalone repos with preserved git history. v0.4+ adds workspace
#     initialization and splitting via the HOBOTS cascade model.
# CREATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# UPDATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON
# VERSION:  0.2.1  (this doc's own revision counter — NOT the CLI version.
#           CLI version lives in ../ROADMAP.md header, currently v0.3.6.
#           Live deliverable/gap tracking now lives in features-map.md.)
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```

**Owner:** Joe Negron (wwwizards)
**Repo:** `wwwizards/pickaxe`
**Current version:** see [`../ROADMAP.md`](../ROADMAP.md) AS-IS (v0.3.6 shipped: `discover` incl. `commit-trends`/`drift`, `diagnose`, `scan`, `backup`, `restore`)
**Live deliverable tracker:** [`features-map.md`](features-map.md) (mermaid visual overview) + [`features-listing.md`](features-listing.md) (full checkbox/Franklin-priority outline) — split 2026-07-29 for side-by-side scrolling, kept in sync manually

------------------------------

## Feature intent

Pickaxe graduates from discovery-only extraction helper into a repeatable context and repo-health utility for multi-repo operations.

## Problem statement

Tooling folders can exist locally without git identity, remotes can disappear from config, and teams lose continuity across sessions.

## Value statement

Pickaxe should make repo state observable, repairable, and auditable with one command surface so teams stop rediscovering the same environment drift.

## Scope in play

- Extraction pipeline maturity (Track A — 0% built as of 2026-07-29, see ROADMAP.md)
- Repo health + hydration commands (Track B — `discover`, `diagnose`, `scan`, `backup`, `restore` shipped)
- Repo-hygiene diagnostics: instruction bloat + rollup (new, 2026-07-29 — see F-03 below and `features-map.md`)
- Context-oracle groundwork tied to ai-labs knowledge sources (Track C, design-only)
- Workspace init/split with HOBOTS cascade scaffold (`v0.4` track, F-02 below)

> **Note (2026-07-29):** the "5D surface: discover, diagnose, design, deliver, document" noun model described in `.HANDOFF/DESIGN.md` is a **design target, not implemented**. The shipped CLI only has `discover`/`diagnose` as real verbs (plus `scan`/`backup`/`restore`, which the 5D model doesn't account for at all); `design`/`deliver`/`document` don't exist yet. See `features-map.md` Track: design/document.

## Non-goals (for now)

- Full dependency manager behavior
- Automatic destructive rewrites of existing repositories
- Hidden remediation without an explicit operator action

------------------------------

## F-01: Discovery and extraction (Track A/B — v0.1–v0.3.6)

See `../ROADMAP.md` § AS-IS and § TO-BE for full details.

**Status (reconciled 2026-07-29):** v0.3.6 shipped — `discover` (incl. `commit-trends`, `drift`, `--submodules-only`), `diagnose`, `scan` (incl. `already_extracted`), `backup`, `restore` — 98 tests green. Extraction pipeline (Track A, `--execute` mode) remains **0% built** — no pipeline scaffolding exists yet; see ROADMAP.md Track A checklist.

## F-03: Repo-hygiene diagnostics — instruction bloat + rollup (added 2026-07-29)

**MVP scope, buildable now, no Federation dependency** (rescoped 2026-07-29 — see ROADMAP.md Track B and `features-map.md` for the full gap breakdown). Two new verbs:

- `diagnose instruction-bloat` — apply the line-count/module-scatter triggers already documented in root `copilot-instructions.md` against `.github/*.instructions.md`, `AGENTS.md`, `SKILL.md` files.
- `deliver instruction-rollup` — the **first-ever `deliver` verb to ship**; extracts a flagged block into a new scoped instruction file using the existing Instruction Inheritance Pattern frontmatter.

See `features-listing.md` for the full checkbox/priority-tracked deliverable list and `features-map.md` for the visual overview — not duplicated here to avoid drift between multiple live-tracking docs.

------------------------------

## F-02: Workspace initialization and splitting (v0.4)

**Design reference:** `wwwizards/ai-labs` `.HANDOFF/DESIGN.md` D-10, `.HANDOFF/FEATURE.md` F-pickaxe-workspace, `.PROTOCOL/README.md` § Inheritance Scope

### What it does

Scaffolds and manages the HOBOTS cascade-inheritance structure — the four context anchor file types (`.PROTOCOL/README.md`, `AGENTS.md`, `DESIGN.md`, `SPEC.md`) that inherit root-to-leaf across a repo or workspace tree.

### Commands

| Command | What it does |
|---|---|
| `pickaxe init <slug>` | Scaffolds `.HANDOFF/<slug>/` with 5-star anchor files (FEATURE + SPEC + DESIGN + STATE + SESSIONS/) + appropriate `.PROTOCOL/` layer |
| `pickaxe workspace init` | Bootstraps a new repo/workspace with Layer 0 `.PROTOCOL/README.md`, root `AGENTS.md`, and `.HANDOFF/` in one command |
| `pickaxe workspace split <sub-path>` | Extracts a subtree into a new workspace/repo; preserves cascade; writes `SPLIT-FROM:`/`SPLIT-TO:` in both STATE.md files |

### Acceptance criteria (hard-pass)

- [ ] `pickaxe init <slug>` creates all 5-star files from template; no manual copy-paste
- [ ] `pickaxe workspace init` produces a valid Layer 0 cascade on first run
- [ ] `pickaxe workspace split` preserves the source cascade at the destination root
- [ ] `SPLIT-FROM:` / `SPLIT-TO:` lineage entries written automatically in both STATE.md files
- [ ] Cascade-aware: reads existing anchor files before writing; `--force` required to overwrite
- [ ] `--dry-run` prints what would be created without touching filesystem
- [ ] All generated files pass `check-headers.py` autodoc validator on first run
- [ ] Nested monorepo: `pickaxe workspace init --subtrees a,b,c` places Layer 1 overrides in each subtree

### Non-goals (v0.4)

- Not a git workflow tool (no branch creation, no PRs)
- Not a deployment tool
- `gh` integration (remote creation on split) deferred to v0.5+

> **Reconciliation note (2026-07-29):** this file previously contained a full verbatim duplicate of the "Feature intent"/"Problem statement"/"Value statement"/"Scope in play"/"Non-goals" blocks below F-02 (a paste artifact — same failure class as the duplicate block found and removed in `.HANDOFF/DESIGN.md` the same day). The duplicate also referenced a stale, never-shipped command set (`doctor`, `inventory`, `hydrate`, `drift`, `report`) that doesn't match any verb in `../ROADMAP.md` or actual `pickaxe.py` argparse subcommands. Removed; canonical copy is the single set of sections above. Full per-verb gap tracking now lives in `features-map.md`, created the same day.