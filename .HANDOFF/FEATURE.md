# FEATURE.md

## Feature intent

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
