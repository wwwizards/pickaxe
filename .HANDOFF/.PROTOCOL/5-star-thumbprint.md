# 5-Star Thumbprint (pickaxe)

## Purpose

Provide minimum continuity metadata so a new human or agent can resume work in under 5 minutes without replaying full chat history.

## Required files

- `.HANDOFF/STATE.md`
- `.HANDOFF/FEATURE.md`
- `.HANDOFF/DESIGN.md`
- `.HANDOFF/SESSIONS/<YYMMDD-topic>.md` *(see adaptation below)*

## Session update contract

Every substantive session should update:

1. `STATE.md` — regenerated, not appended; it is the running sum of all sessions
2. a flat `SESSIONS/YYMMDD-topic.md` session record (detail that would bloat STATE.md)
3. next actions and blockers

## Local adaptation — flat session files

- **Canonical spec:** `.HANDOFF/SESSIONS/<YYMMDD-topic>/SESSION.md` (nested folder)
- **This project:** `.HANDOFF/SESSIONS/YYMMDD-topic.md` (flat file)
- **Rationale:** Nested folders are appropriate for swarm scenarios where a session generates multiple artifacts (agent-specific files, diffs, reports). For solo/small-team projects a single flat file is sufficient and avoids navigation noise.
- **Exception:** Use a subfolder if a session produces 2+ files (e.g. a SESSION.md + a generated report or diff).

## Quality bar

A handoff is 5-star when it includes:

- what changed
- why it changed
- what to do next
- blockers/risks
- exact file paths touched
