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
# UPDATED:  260612 BY: Claude(Sonnet4.6)::Copilot::SOLOMON
# VERSION:  0.2.0
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```

**Owner:** Joe Negron (wwwizards)
**Repo:** `wwwizards/pickaxe`
**Current version:** v0.2.0 (discover + diagnose shipped)

------------------------------

## Feature intent

Pickaxe graduates from discovery-only extraction helper into a repeatable context and repo-health utility for multi-repo operations.

## Problem statement

Tooling folders can exist locally without git identity, remotes can disappear from config, and teams lose continuity across sessions.

## Value statement

Pickaxe should make repo state observable, repairable, and auditable with one command surface so teams stop rediscovering the same environment drift.

## Scope in play

- Extraction pipeline maturity (`v0.2` track)
- Repo health + hydration commands (5D surface: discover, diagnose, design, deliver, document)
- Context-oracle groundwork tied to ai-labs knowledge sources
- Workspace init/split with HOBOTS cascade scaffold (`v0.4` track)

## Non-goals (for now)

- Full dependency manager behavior
- Automatic destructive rewrites of existing repositories
- Hidden remediation without an explicit operator action

------------------------------

## F-01: Discovery and extraction (v0.1–v0.3)

See `ROADMAP.md` § AS-IS and § TO-BE for full details.

**Status:** v0.2.0 shipped (discover + diagnose commands, 30 tests green). Extraction pipeline (v0.2 execute track) in design.

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


Pickaxe graduates from discovery-only extraction helper into a repeatable context and repo-health utility for multi-repo operations.

## Problem statement

Tooling folders can exist locally without git identity, remotes can disappear from config, and teams lose continuity across sessions.

## Value statement

Pickaxe should make repo state observable, repairable, and auditable with one command surface so teams stop rediscovering the same environment drift.

## Scope in play

- Extraction pipeline maturity (`v0.2` track)
- Repo health + hydration commands (`doctor`, `inventory`, `hydrate`, `drift`, `report`)
- Context-oracle groundwork tied to ai-labs knowledge sources

## Non-goals (for now)

- Full dependency manager behavior
- Automatic destructive rewrites of existing repositories
- Hidden remediation without an explicit operator action