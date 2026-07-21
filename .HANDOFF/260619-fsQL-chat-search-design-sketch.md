# Design Sketch — pickaxe.fsql : Copilot Chat History Search

**Date:** 2026-06-19
**Status:** DESIGN SKETCH — pending backlog ticket creation + design approval
**Author:** Sol-02 session (Joe Negron, LogicWizards.NYC)
**Context:** Spawned from extension security audit (session 260618-260619).
User attempted `Ctrl+F` in Copilot chat panel — not available. Evaluated 5
third-party extensions (GHCP Dashboard, Copilot Chat History, Copilot Memory
Board, PromptVault, ACCM). ACCM confirmed telemetry exfil to `telemetry.acidni.net`.
Conclusion: build it in-house as a `pickaxe` add-on, zero third-party trust required.

---

## The Query the User Described

```
pickaxe fsql SELECT [timestamp, chatname, matchQty, score]
FROM [copilot.chat a, *.memories.* m, *SESSION* s, STATE, *EPIC*, *FEAT*, *STORY*]
WHERE <filter> FUZZY-OPERATOR <keywords list>
ORDER BY matchQty DESC, score DESC, chatname, timestamp
GROUP BY chatname
HAVING timestamp > 7d
```

---

## Data Sources (all local, all read-only)

| Alias | Path | Content |
|---|---|---|
| `copilot.chat` | `%APPDATA%\Code\User\workspaceStorage\*\chatSessions\*.json` | Agent/Ask/Chat sessions. Fields: `customTitle`, `requests[].message.text`, `requests[].response.value` |
| `copilot.agent` | `%APPDATA%\Code\User\workspaceStorage\*\agentSessions.model.cache` | Agent sessions with checkpoints |
| `*.memories.*` | `/memories/**/*.md` | Copilot memory files (user + session + repo scopes) |
| `*SESSION*` | `.AI-TRAINING/**/*Handoff*.json` | Handoff JSONs (completedWork, marchingOrders, keyDecisions) |
| `STATE` | `.HANDOFF/STATE.md` + `**/STATE.md` | Per-project session state files |
| `*EPIC*` `*FEAT*` `*STORY*` | `**/BACKLOG/**/*.md`, `**/IN-PROGRESS/**/*.md` | Agile tickets (filename glob-matched) |

---

## Proposed Module: `pickaxe.fsql`

### Layer 1 — Index (CDC-style, lazy)

```
~/.pickaxe/index/
  chat-sessions.jsonl     # one line per session: {id, workspace, title, mtime, path}
  chat-messages.jsonl     # one line per message: {sessionId, role, text, timestamp}
  memories.jsonl          # one line per memory file: {scope, path, mtime, content}
  tickets.jsonl           # one line per ticket: {status, date, type, title, path}
```

Built on first run, refreshed on `--reindex`. Files are ~200 bytes/entry → 10k
entries = ~2MB. Scannable in <50ms with simple grep/jq.

### Layer 2 — Query Parser

Accepts simplified SQL-ish surface:

```
SELECT <fields>
FROM <sources>           # comma-separated source aliases or globs
WHERE <expr>             # field comparisons + FUZZY operator
ORDER BY <cols>          # supports DESC/ASC
GROUP BY <col>
HAVING <expr>            # post-group filter (e.g. timestamp > 7d)
LIMIT <n>
```

**FUZZY operator** (the key differentiator):
```
WHERE text FUZZY "agent bootstrap terminal" THRESHOLD 0.6
```
Translates to: score each document against the keyword list using TF-IDF or
token overlap. Return `matchQty` (# keywords matched) and `score` (0.0–1.0).
No external libs required — stdlib token overlap is sufficient for MVP.

### Layer 3 — Output Formats

```
pickaxe fsql "..." --format table   # default: terminal table
pickaxe fsql "..." --format json    # pipe to other tools
pickaxe fsql "..." --format md      # markdown report
pickaxe fsql "..." --format grep    # file:line refs for editor jump
```

---

## MVP Scope (Track E — proposed new pickaxe roadmap track)

| Step | What | Est |
|---|---|---|
| E-01 | Index builder: scan chatSessions → chat-sessions.jsonl + chat-messages.jsonl | 2h |
| E-02 | Index builder: scan memories/ + tickets | 1h |
| E-03 | Query parser: FROM aliases, WHERE field=, HAVING timestamp> | 2h |
| E-04 | FUZZY operator: token overlap scoring, matchQty + score columns | 2h |
| E-05 | CLI: `pickaxe fsql "<query>"` + `pickaxe fsql --reindex` | 1h |
| E-06 | Output: table + json + grep formats | 1h |
| E-07 | Tests: pytest suite, smoke + integration | 2h |
| **Total** | | **~11h** |

---

## Relation to Existing Work

- **fsQL / fsQL** (`.HANDOFF/fsDB-org-bootstrap/WHITEPAPER.md`): This is the
  first concrete *consumer* of fsQL on a non-ticket data source (Copilot chat).
  Validates the "filesystem IS the database" pattern on VS Code's own storage.
- **fsDB rename blocker** (`NEW-260601-fsDB-B2S02-STORY-Rename-fsQL-to-fsQL-Codebase-Sweep.md`):
  This sketch uses `fsql` as the CLI verb — consistent with the pending rename.
- **pickaxe ROADMAP Track C** (Context oracle): `pickaxe fsql` is a natural
  Track C addition — querying agent context artifacts (chats, memories, handoffs).
- **Dashboard Fuzzy Search** (`NEW-251125-Dashboard-C2F05-FEATURE-Fuzzy-Search-MD-Viewer.md`):
  Overlapping need — that ticket is about `.md` files in the repo; this covers
  Copilot chat sessions. Both feed the same "find something I said/wrote" UX.
- **adventure D-07 Q3**: "FSQL federation scope (local-only vs. federated-remote)"
  — this MVP is explicitly local-only. Remote federation is deferred.

---

## Sidebar Extension (Longer-Term)

The user asked for "a sexier sidebar extension". That is a separate Track F:
- VS Code WebView panel: search box + results list + message preview
- Backed by `pickaxe fsql` index (reads `.jsonl` files, no subprocess)
- No third-party extension trust required — built by us, in our sandbox
- Prerequisite: Track E (CLI) must be green first

---

## Suggested Backlog Ticket

```
NEW-260619-pickaxe-B1F05-FEATURE-fsql-chat-search-index.md
Priority: B1 (strategic, high value, not MVP-blocking)
Size: L (5 points, ~11h)
Parent: pickaxe ROADMAP Track C/E
Blocked by: none (can start any time)
```
