# STATE.md

## Snapshot

- Project: pickaxe
- Date: 2026-05-26
- Phase: bootstrap + roadmap consolidation
- Status: active

## What changed in this session

- Added checklist-driven execution tracker to ROADMAP.md.
- Added initial 5-star handoff scaffold under .HANDOFF/.
- Captured repo-hydration + drift-control feature track as first-class roadmap items.

## Current focus

- Keep extraction pipeline track intact while adding reusable repo hygiene and drift controls.
- Evolve pickaxe as an independent workstream with its own continuity artifacts.

## Next 3 actions

1. Define canonical manifest format for repo hydration (`repos.manifest.json`).
2. Implement `pickaxe inventory` output (`table` + `json`).
3. Implement `pickaxe doctor` checks for missing `.git`, missing `origin`, and stripped config.

## Risks / blockers

- Local folder may exist without `.git` metadata (false sense of repo presence).
- Mixed layout (monorepo + nested repos) increases false positives without explicit health checks.

## Handoff note

See .HANDOFF/FEATURE.md and .HANDOFF/DESIGN.md before implementing command surface changes.
