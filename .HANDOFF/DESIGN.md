# DESIGN.md

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

## Command model (target)

- `pickaxe doctor`
- `pickaxe inventory --format table|json`
- `pickaxe hydrate --manifest repos.manifest.json --dry-run`
- `pickaxe drift --manifest repos.manifest.json`
- `pickaxe report --out reports/`
- `pickaxe audit`

## Design guardrails

- dry-run first for all mutating operations
- no forced overwrite of existing directories
- all remediation actions logged with timestamp + rationale
- keep output agent-agnostic (human-readable + machine-readable)
