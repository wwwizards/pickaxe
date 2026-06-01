# etl-tools

JSON → table / CSV / JSON formatter. Part of the [pickaxe](../README.md) monorepo.

Consumes structured JSON data — from a file or stdin — and renders it as an
aligned terminal table, CSV, or normalized JSON. The formatter half of the
pickaxe pipeline: any tool that emits JSON can pipe into this.

---

## Requirements

Python 3.7+, stdlib only. No pip installs needed.

---

## Quick start

```powershell
# From a file
python etl-tools\convert_from_json.py -f data.json -o table

# From stdin (pipe from any JSON producer)
python producer.py | python etl-tools\convert_from_json.py -f - -o table

# Select and order columns
python etl-tools\convert_from_json.py -f data.json -o table -c "name,status,region"

# Filter rows, then render as CSV
python etl-tools\convert_from_json.py -f data.json -o csv -q "status = active"
```

---

## CLI reference

```
convert_from_json.py -f FILE -o FORMAT [-q QUERY] [-c COLUMNS] [-v | -vv]

  -f, --file      Path to JSON file, or - for stdin
  -o, --output    Output format: table | csv | json  (default: json)
  -q, --query     Filter expression (see Query syntax below)
  -c, --columns   Comma-separated field names to display, in order
  -v              Verbose: print condition results per row
  -vv             Extra verbose: print full query evaluation trace
```

---

## Output formats

**table** — aligned box-drawing table, best for terminal display:
```
┌──────────────────────────────────────────┐
│ label        │ cpu_util_pct │ gpu0_util_pct │
├──────────────────────────────────────────┤
│ baseline     │ 19.1         │ 0             │
└──────────────────────────────────────────┘
```

**csv** — RFC 4180, Unix `\n` line endings on all platforms (safe to pipe to other tools):
```
label,cpu_util_pct,gpu0_util_pct
baseline,19.1,0
```

**json** — pretty-printed, indent=4.

---

## Query syntax

Case-sensitive. Wildcard matching via `fnmatch` (`*` and `?`).

```
-q "FIELD = value"           exact match
-q "FIELD != value"          not equal
-q "FIELD = 10.*"            glob match
-q "status = active and region = eastus"
-q "type = bug or type = incident"
```

---

## Column selection

`-c` controls which fields appear and in what order. Fields not present in the
data are silently skipped. Without `-c`, all fields are shown in sorted order.

```powershell
-c "timestamp,label,cpu_util_pct,gpu0_util_pct,gpu0_temp_c"
```

---

## Pipeline usage with sys-tools

sys-tools `sys-probe.py` emits JSON that pipes directly into this formatter:

```powershell
# Real-time snapshot as table
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "post-tier1" --no-intel `
  | .venv\Scripts\python.exe etl-tools\convert_from_json.py -f - -o table `
  -c "timestamp,label,cpu_util_pct,gpu0_util_pct,gpu0_vram_used_mb,gpu0_temp_c,gpu0_pstate"

# Accumulated probes file as table
.venv\Scripts\python.exe etl-tools\convert_from_json.py `
  -f .AI-TRAINING\probes.json -o table `
  -c "timestamp,label,cpu_util_pct,gpu0_util_pct,gpu0_temp_c,gpu0_pstate"
```

---

## Module usage

```python
from etl_tools.convert_from_json import from_json, filter_data, print_table

# Render a file
from_json("data.json", output="table", columns="name,status,region")

# Filter then render in-memory data
filtered = filter_data(data, query="status = active")
print_table(filtered, columns=["name", "status"])
```

---

## Files

| File | Purpose |
|---|---|
| `convert_from_json.py` | Main tool — v0.4.2 |
| `__init__.py` | Package init for module import |
| `.HANDOFF/DESIGN.md` | Architecture and pipe contract |
| `.HANDOFF/STATE.md` | Current version, what shipped, open items |
| `.HANDOFF/ROADMAP.md` | Planned: numeric filters, sort, markdown output, diff mode |
