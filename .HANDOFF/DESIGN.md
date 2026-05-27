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
