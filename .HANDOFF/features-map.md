# pickaxe — Features Map (visual overview)

```
# --------------------------------------------------------------------------
# NOTES:    features-map.md
# --------------------------------------------------------------------------
# ABSTRACT: Mermaid visual overview of pickaxe deliverables and gaps —
#     PICKAXE root fanning into per-verb columns (discover/diagnose/scan/
#     backup-restore/deliver/design-document/extraction/workspace), boxes
#     color-coded green/amber/red/grey. Diagram-only by design (split out
#     of a combined doc on 2026-07-29) so it can scroll side by side with
#     features-listing.md, which carries the full checkbox outline, Franklin
#     priorities, and open decisions. Companion to FEATURE.md (intent/scope)
#     and ROADMAP.md (AS-IS/TO-BE narrative).
# CREATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON
# UPDATED:  260729 BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON
# ARCHITECT: Joe Negron -- LogicWizards.NYC
# TECHLEAD:  JN (Joe Negron -- LogicWizards.NYC)
# VERSION:  0.3.6  (mirrors the pickaxe CLI version; ../ROADMAP.md is
#           canonical. All .HANDOFF docs bump together at every wrap.)
# STAGE:    ACTIVE
# --------------------------------------------------------------------------
```

> **See also:** [`features-listing.md`](features-listing.md) for the full checkbox tracker, Franklin priorities (A1-A4 current sprint, B/C backlog), and open decisions. Kept in sync manually — update both when a verb's status changes.

## Color key

- 🟢 green = shipped, no known gap · 🟡 amber = MVP-scoped/in progress · 🔴 red = blocked (named prerequisite missing) · ⚪ grey = undefined/backlogged

## Visual overview

Swimlanes are verb tracks off the `PICKAXE` root; box fill + text color signal status per the key above. Labels hard-wrap with `\n` near 20-25 chars/line per repo convention (see `AGENTS.md` § Markdown Style).

```mermaid
flowchart LR
    ROOT["PICKAXE\nCLI"]

    subgraph DISCOVER["discover"]
    direction TB
        D1["repo map + health\nflags (v0.2.0)"]
        D2["commit-trends\n(v0.3.3)"]
        D3["drift (v0.3.6)"]
        D4["submodules-only\n(v0.3.4)"]
        D5["ownership\n(undefined, B1)"]
        D6["split-candidates\n(undefined, B2)"]
    end

    subgraph DIAGNOSE["diagnose"]
    direction TB
        G1["core diagnose\n(v0.2.0)"]
        G2["noun-dispatch\nretrofit (A1)"]
        G3["instruction-bloat\nMVP (A3)"]
        G4["handoff-drift\n(undefined, B3)"]
        G5["ticket-drift\n(backlogged, C2)"]
        G6["shell-sprawl\n(backlogged, C3)"]
    end

    subgraph DELIVER["deliver"]
    direction TB
        L1["deliver subparser\n(new verb, A2)"]
        L2["instruction-rollup\nMVP (A4)"]
        L3["handoff-rollup\n(undefined, B6)"]
        L4["dirs/drift/docs\n(undefined, B7-9)"]
    end

    subgraph SCAN["scan"]
    direction TB
        S1["tool scorer\n(v0.1.0)"]
        S2["already_extracted\n(v0.3.4)"]
        S3["skip-by-default\n(undefined, C4)"]
    end

    subgraph BKRS["backup/restore"]
    direction TB
        BK1["backup\n(v0.3.5)"]
        BK2["restore\n(v0.3.5)"]
    end

    subgraph DSDOC["design/document"]
    direction TB
        DD1["5D model\n(not implemented)"]
    end

    subgraph EXTRACT["extraction (A)"]
    direction TB
        E1["--execute mode\n(0% built)"]
    end

    subgraph WKSP["workspace init/split"]
    direction TB
        W1["init/split\n(undefined)"]
    end

    ROOT --> DISCOVER
    ROOT --> DIAGNOSE
    ROOT --> DELIVER
    ROOT --> SCAN
    ROOT --> BKRS
    ROOT --> DSDOC
    ROOT --> EXTRACT
    ROOT --> WKSP

    classDef root fill:#cfe2ff,stroke:#0d47a1,color:#0d1b3d,stroke-width:3px;
    classDef green fill:#b7e4c7,stroke:#2d6a4f,color:#1b4332,stroke-width:2px;
    classDef amber fill:#ffe29a,stroke:#b8860b,color:#5c4400,stroke-width:2px;
    classDef red fill:#ffb3b3,stroke:#b00020,color:#5c0000,stroke-width:2px;
    classDef grey fill:#e2e2e2,stroke:#888888,color:#3a3a3a,stroke-width:2px;

    class ROOT root
    class D1,D2,D3,D4 green
    class D5,D6 grey
    class G1 green
    class G2 red
    class G3 amber
    class G4,G5,G6 grey
    class L1 red
    class L2 amber
    class L3,L4 grey
    class S1,S2 green
    class S3 grey
    class BK1,BK2 green
    class DD1 grey
    class E1 red
    class W1 grey
```

---

**Full checkbox tracker, priorities, and open decisions:** [`features-listing.md`](features-listing.md)
