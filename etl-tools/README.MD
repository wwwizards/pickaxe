<!-- BEGIN AutoDoc-head2md AutoGen -->
<div style="float:left; width:100%; padding:5px">

# SCRIPT: __init__.py

| Key | Value |
| --- | ----- |
| PURPOSE | initializer - part of the converters package, to facilitate       exposing methods when imported into other scripts so that we can       easily access them directly |
| LICENSE | COPYLEFT - GNU Lesser General Public License (LGPL) |
| CREATED | 24-1005 BY: github.com/wwwizards |
| VERSION | v0.3.1 (module ready) |

*Generated on 2024-10-05 03:34:40 EDT*
</div>


<!-- BEGIN AutoDoc-head2md AutoGen -->
<div style="float:left; width:100%; padding:5px">

# MODULE: convert_from_json.py

| Key | Value |
| --- | ----- |
| PURPOSE | A module for converting JSON data into various formats: JSON, CSV, or     a table. It supports filtering data using user-defined queries and     optional verbosity for debugging or condition evaluation. |
| USAGE | - As a command-line tool:       python fromJSON.py -f [path/to/json] -o [json|csv|table] -q [query] [-v | -vv]      - As an imported module:       from converters.fromJSON import from_json       from_json(file_path, format="table", query="field", verbose=0) |
| ARGUMENTS | -f, --file      : Path to the input JSON file.     -o, --output    : Output format (default: json). Options: json, csv, table.     -q, --query     : Wildcard query string for filtering data.     -v              : Verbose mode; prints condition results for each item.     -vv             : Extra verbose mode; prints detailed evaluation logs. |
| LICENSE | COPYLEFT - GNU Lesser General Public License (LGPL) |
| CREATED | 24-0905 BY: github.com/wwwizards |
| UPDATED | 24-1005 BY: github.com/wwwizards |
| VERSION | v0.3.1 (module ready) |

## FUNCTION: print_json()

| Key | Value |
| --- | ----- |
| DESCRIPTION | prints data in JSON format |

## FUNCTION: print_csv(data, index_first=True)

| Key | Value |
| --- | ----- |
| DESCRIPTION | prints data in CSV format |

## FUNCTION: print_table(data, index_first=True)

| Key | Value |
| --- | ----- |
| DESCRIPTION | prints data in an aligned table format |

## FUNCTION: filter_data(data, query, verbose=False, extra_verbose=False)

| Key | Value |
| --- | ----- |
| PURPOSE | to filter data based on a query string |

## FUNCTION: apply_conditions(item, conditions, verbose=False, extra_verbose=False)

| Key | Value |
| --- | ----- |
| PURPOSE | to evaluate conditions on data entries |

## FUNCTION: evaluate_expression(item, tokens, verbose=False, extra_verbose=False)

| Key | Value |
| --- | ----- |
| PURPOSE | to evaluate a logical expression recursively |

## FUNCTION: build_condition_function(condition)

| Key | Value |
| --- | ----- |
| PURPOSE | to parse and build a condition function |

## FUNCTION: parse_query(query)

| Key | Value |
| --- | ----- |
| PURPOSE | to parse a query into evaluable conditions |

## FUNCTION: from_json(file_path, output="json", query=None, verbose=0)

| Key | Value |
| --- | ----- |
| PURPOSE | exposed function to provide the same functionality main(), but       primarily to used when included in other scripts as a module |
| USAGE | converters.from_json(file="path/to/file.json", output="table", query="FIELD = value", verbose=1) |

## FUNCTION: main()

| Key | Value |
| --- | ----- |
| PURPOSE | Main function to handle argument parsing and call appropriate functions |

*Generated on 2024-10-05 03:34:40 EDT*
</div>
