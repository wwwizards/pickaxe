# pickaxe — Feature Listing (checkbox tracker)

```
# --------------------------------------------------------------------------
# NOTES:    features-listing.md
# --------------------------------------------------------------------------
# ABSTRACT: Live, per-verb checkbox tracker for pickaxe deliverables and
#     gaps — priorities via the Franklin method (A1,A2...B1,B2...C1,C2...).
#     Split out of features-map.md on 2026-07-29 so the mermaid diagram
#     (features-map.md) and this text outline can be viewed side by side
#     with independent scrolling. Companion to features-map.md (visual
#     overview) and FEATURE.md (intent/scope); ROADMAP.md carries the
#     AS-IS/TO-BE narrative this file distills into trackable checkboxes.
# CREATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON
# UPDATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON
# ARCHITECT: Joe Negron -- LogicWizards.NYC
# TECHLEAD:  JN (Joe Negron -- LogicWizards.NYC)
# VERSION:  0.3.6  (mirrors the pickaxe CLI version; ../ROADMAP.md is
#           canonical. All .HANDOFF docs bump together at every wrap.)
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```

> **See also:** [`features-map.md`](features-map.md) for the mermaid visual overview (same color/priority scheme, diagram only). Open both side by side — they're kept in sync manually, update both when a verb's status changes.

## Legend

- 🟢 **Green** — shipped, tests green, no known gap
- 🟡 **Amber** — in progress / partially built / MVP-scoped and ready to build
- 🔴 **Red** — blocked (a real, named prerequisite is missing)
- ⚪ **Grey** — undefined / not yet designed / intentionally backlogged

**Priority (Franklin method):** A-tier = current sprint focus, in order (A1 before A2). B/C-tier = real but deliberately deferred — not ranked further until promoted. Grey items get no letter until someone decides to scope them.

---

## 🎯 Current sprint focus (A-tier only)

- [ ] **A1** — retrofit `diagnose` with noun-dispatch (`DIAGNOSE_NOUNS`), mirroring `discover`'s existing pattern
- [ ] **A2** — add the first-ever top-level `deliver` subparser + `_cmd_deliver` dispatch
- [ ] **A3** — `diagnose instruction-bloat` (depends on A1)
- [ ] **A4** — `deliver instruction-rollup` (depends on A2 + A3's output contract)

Everything below A-tier is reference/backlog — captured so it isn't lost, not something to decide today.

---

## Track: `discover` 🟢 shipped, healthy

- [x] repo map + health flags — v0.2.0
- [x] `discover commit-trends` — v0.3.3
- [x] `discover drift` — v0.3.6
- [x] `--submodules-only` — v0.3.4
- [ ] ⚪ `discover ownership` — undefined, Track B backlog — **B1**
- [ ] ⚪ `discover split-candidates` — undefined, Track B backlog — **B2**
- [ ] ⚪ `discover tools` (YAML→MD manifest, Track E) — undefined, no schema decided — **C1**

## Track: `diagnose` 🟡 core shipped, structural retrofit needed for new verbs

- [x] core diagnose (missing `.git`/origin/config) — v0.2.0; gitlink fix v0.3.2
- [ ] 🔴 **A1** — noun-dispatch retrofit (`DIAGNOSE_NOUNS` + `noun` arg, mirroring `discover`) — blocks A3
- [ ] 🟡 **A3** — `diagnose instruction-bloat` (MVP scoped 2026-07-29, blocked on A1)
  - [ ] file-count / whole-file line-threshold check (simple)
  - [ ] section/heading line-count parser for the ">50-line scattered pattern" rule (new complexity — no H2/H3 boundary parser exists yet)
  - [ ] `--format table|json` + `--save` convention (established pattern, easy to forget)
- [ ] ⚪ `diagnose handoff-drift` — undefined, Track B backlog — **B3**
- [ ] ⚪ `diagnose write-conflict` (compare-before-write fingerprints) — undefined, Track B backlog — **B4**
- [ ] ⚪ `diagnose ticket-drift` — **backlogged 2026-07-29 (user call)**, buildable-now, not a priority right now — **C2**
- [ ] ⚪ `diagnose shell-sprawl` — **backlogged 2026-07-29 (user call)**, buildable-now, not a priority right now — **C3**
- [ ] ⚪ venv/dependency-tree exclusion detection — undefined, Track B backlog — **B5**

## Track: `deliver` 🔴 verb does not exist yet at all

- [ ] 🔴 **A2** — top-level `deliver` subparser + `_cmd_deliver` dispatch — blocking prerequisite for every `deliver-*` verb below
- [ ] 🟡 **A4** — `deliver instruction-rollup` (MVP scoped 2026-07-29, blocked on A2 + A3's finding-schema output)
  - [ ] diagnose→deliver JSON handoff contract (finding schema: `file`, `start_line`, `end_line`, `reason`)
  - [ ] frontmatter auto-fill rules (`applyTo`/`description`/`tags`/`maintainer` — which are inferred vs. placeholder)
  - [ ] dry-run-by-default (D-01) + `--execute` to write
  - [ ] idempotent pointer check (skip if block already extracted — repo's own Idempotent Script Pattern rule)
- [ ] ⚪ `deliver handoff-rollup` — undefined, Track B backlog — **B6**
- [ ] ⚪ `deliver dirs` (clone missing repos from manifest) — undefined, Track B/E backlog — **B7**
- [ ] ⚪ `deliver drift` (apply drift-report fixes) — undefined — **B8**
- [ ] ⚪ `deliver docs` (baseline hygiene files) — undefined — **B9**

## Track: `scan` 🟢 shipped, one known gap

- [x] tool-worthiness scorer — v0.1.0
- [x] `already_extracted` annotation — v0.3.4
- [ ] ⚪ standalone-repo **skip**-by-default (today only annotates, doesn't omit) — Track A backlog — **C4**

## Track: `backup` / `restore` 🟢 shipped, no known gaps

- [x] `backup <root> --to <dest>` — v0.3.5
- [x] `restore <backup> --to <dest>` — v0.3.5

## Track: `design` / `document` ⚪ conceptual only, not real verbs

- [ ] ⚪ Confirmed 2026-07-29 (DESIGN.md reconciliation): the "5D surface" noun model is a design target only. No decision yet whether `design`/`document` ever become real top-level verbs, or stay phase-names used only in prose. Not scoped, not prioritized.

## Track: extraction pipeline (Track A) 🔴 largest unbuilt surface, out of current sprint

- [ ] 🔴 `--execute` mode, `.pickaxe/` chain-of-custody, AI-context detection, cluster detection — 0% built, no pipeline scaffolding exists. Reference only — not in scope this sprint.

## Track: workspace init/split (F-02, v0.4 target) ⚪ deferred, reference only

- [ ] ⚪ `pickaxe init <slug>`
- [ ] ⚪ `pickaxe workspace init`
- [ ] ⚪ `pickaxe workspace split <sub-path>`

(All undefined at the implementation level — acceptance criteria exist in `FEATURE.md` F-02 but no code, no priority assigned. Not in scope this sprint.)

---

## Decisions still needed before A3/A4 can start (answer here, don't re-derive)

- [ ] Scan scope for `diagnose instruction-bloat`: single-repo (cwd, like `diagnose`) or workspace-wide (like `scan`/`backup`)? Nested submodule `.github/` dirs won't be found by cwd-only scanning.
- [ ] Handoff format between A3 and A4: `--from-report findings.json` vs. manual `--file/--start/--end` flags?
- [ ] Default line-count threshold: hardcoded 1000, or a `--max-lines` flag? Default for the per-section (>50-line) rule?
