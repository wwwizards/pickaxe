# 5-Star Thumbprint (pickaxe)

## Purpose

Provide minimum continuity metadata so a new human or agent can resume work in under 5 minutes without replaying full chat history.

## Required files

- `.HANDOFF/STATE.md`
- `.HANDOFF/FEATURE.md`
- `.HANDOFF/DESIGN.md`
- `.HANDOFF/SESSIONS/<YYMMDD-topic>/SESSION.md`

## Session update contract

Every substantive session should update:

1. `STATE.md` snapshot section
2. a new or existing `SESSIONS/*/SESSION.md` log entry
3. next actions and blockers

## Quality bar

A handoff is 5-star when it includes:

- what changed
- why it changed
- what to do next
- blockers/risks
- exact file paths touched
