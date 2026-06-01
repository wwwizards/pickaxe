# etl-tools — DESIGN.md

CREATED: 2026-06-01
MODULE: etl-tools (part of pickaxe monorepo)
PARENT: pickaxe/.HANDOFF/DESIGN.md (repo-level architecture)

---

## Purpose

etl-tools is the presentation sub-module within pickaxe. It consumes structured
data (JSON arrays or dicts) and renders it as human-readable table, CSV, or
normalized JSON.

It is the **pipe sink** in the pickaxe pipeline. It does not produce data,
interrogate the machine, or call external APIs. Its only job is formatting.

```
[producer]  →  stdout JSON  →  [etl-tools]  →  stdout table/csv/json
sys-probe.py                    convert_from_json.py
pickaxe discover                convert_from_json.py
any JSON emitter                convert_from_json.py
```

---

## Architecture

### Layer 1: Ingestion

Accepts JSON from:
- File path (`-f path/to/file.json`)
- stdin (`-f -`) for pipeline use
- Programmatic call (`from_json(file_path, ...)` when imported as a module)

Input must be a JSON array of flat dicts, or a JSON dict (auto-converted to
indexed array). Nested values are flattened to comma-joined strings by `_cell()`.

### Layer 2: Filter Engine

Optional `-q / --query` applies structured field-condition filtering before
rendering. Supports:
- Equality: `FIELD = value`
- Inequality: `FIELD != value`
- Glob matching: `FIELD = 10.*` (fnmatchcase, case-sensitive)
- Logical operators: `FIELD = x and FIELD2 != y`
- Logical OR: `FIELD = x or FIELD = y`

Parse chain: `parse_query()` → `build_condition_function()` → `evaluate_expression()`

### Layer 3: Formatter

Three renderers, all driven through the same `columns` selection list:

| Renderer | Function | Notes |
|---|---|---|
| `table` | `print_table()` | Box-drawing chars, aligned columns |
| `csv` | `print_csv()` | Unix `\n` line endings on all platforms (v0.4.2) |
| `json` | `print_json()` | Pretty-printed, indent=4 |

Column selection (`-c / --columns`) controls both which fields appear and their
display order. Columns not present in the data are silently skipped.

---

## Pipe Contract

- **Input contract:** stdin must be a valid JSON array. If empty or malformed,
  Python raises `JSONDecodeError` — caller is responsible for non-empty output.
- **Output contract:** stdout is UTF-8. Table/JSON use platform line endings
  (irrelevant for terminal display). CSV uses `\n` unconditionally (v0.4.2+).
- **Never imports from sys-tools.** ETL tools must remain data-agnostic —
  the formatter cannot know or care what generated the JSON.

---

## Module API

When imported (not CLI):

```python
from etl_tools.convert_from_json import from_json, filter_data, print_table

# Render a file
from_json("path/to/data.json", output="table", columns="field1,field2")

# Filter and render in-memory data
filtered = filter_data(data, query="status = active and region = eastus")
print_table(filtered, columns=["name", "status", "region"])
```

---

## OS Compatibility

Pure stdlib only: `json`, `csv`, `re`, `sys`, `argparse`, `fnmatch`.
No platform-specific calls. CSV line ending normalization uses
`sys.stdout.reconfigure(newline='\n')` (Python 3.7+ stdlib, no extra deps).
