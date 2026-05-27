#!/usr/bin/env python3
# --------------------------------------------------------------------------
# MODULE: convert_from_json.py
# --------------------------------------------------------------------------
# PURPOSE:
#     A module for converting JSON data into various formats: JSON, CSV, or
#     a table. It supports filtering data using user-defined queries and
#     optional verbosity for debugging or condition evaluation.
#
# USAGE:
#     - As a command-line tool:
#       python fromJSON.py -f [path/to/json] -o [json|csv|table] -q [query] [-v | -vv]
#
#     - As an imported module:
#       from converters.fromJSON import from_json
#       from_json(file_path, format="table", query="field", verbose=0)
#
# ARGUMENTS:
#     -f, --file      : Path to the input JSON file.
#     -o, --output    : Output format (default: json). Options: json, csv, table.
#     -q, --query     : Wildcard query string for filtering data.
#     -v              : Verbose mode; prints condition results for each item.
#     -vv             : Extra verbose mode; prints detailed evaluation logs.
#
# LICENSE: COPYLEFT - GNU Lesser General Public License (LGPL)
# CREATED: 24-0905 BY: github.com/wwwizards
# UPDATED: 24-1005 BY: github.com/wwwizards
# VERSION: v0.3.1 (module ready)
# --------------------------------------------------------------------------

import json 
import csv 
import re 
import sys 
import argparse
from fnmatch import fnmatchcase

# --------------------------------------------------------------------------
# FUNCTION:  print_json() - prints data in JSON format
# --------------------------------------------------------------------------
def print_json(data):
    print(json.dumps(data, indent=4))

# --------------------------------------------------------------------------
# FUNCTION: print_csv(data, index_first=True) - prints data in CSV format
# --------------------------------------------------------------------------
def print_csv(data, index_first=True):
    if isinstance(data, dict):
        data = [dict(index=index, **details) for index, details in data.items()]

    fieldnames = sorted({key for entry in data for key in entry.keys()})

    if index_first and 'index' in fieldnames:
        fieldnames.remove('index')
        fieldnames = ['index'] + fieldnames

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=',')
    writer.writeheader()
    for row in data:
        writer.writerow(row)

# --------------------------------------------------------------------------
# FUNCTION: print_table(data, index_first=True) - prints data in an aligned table format
# --------------------------------------------------------------------------
def print_table(data, index_first=True):
    if isinstance(data, dict):
        data = [dict(index=index, **details) for index, details in data.items()]

    headers = {key for d in data for key in d.keys()}
    headers = sorted(headers)

    if index_first and 'index' in headers:
        headers.remove('index')
        headers = ['index'] + headers

    col_widths = {header: max(len(header), max(len(str(row.get(header, ""))) for row in data)) for header in headers}

    header_row = " │ ".join(header.ljust(col_widths[header]) for header in headers)
    top_divider = f"┌{'─' * (len(header_row) + 2)}┐"
    mid_divider = f"├{'─' * (len(header_row) + 2)}┤"
    bottom_divider = f"└{'─' * (len(header_row) + 2)}┘"

    print("\n" + top_divider)
    print(f"│ {header_row} │")
    print(mid_divider)

    for row in data:
        row_line = " │ ".join(str(row.get(header, "")).ljust(col_widths[header]) for header in headers)
        print(f"│ {row_line} │")

    print(bottom_divider)

# --------------------------------------------------------------------------
# FUNCTION: filter_data(data, query, verbose=False, extra_verbose=False)
#  PURPOSE: to filter data based on a query string
# --------------------------------------------------------------------------
def filter_data(data, query, verbose=False, extra_verbose=False):
    if isinstance(data, dict):
        data = [dict(index=index, **details) for index, details in data.items()]

    conditions = parse_query(query)
    return [item for item in data if apply_conditions(item, conditions, verbose, extra_verbose)]

# --------------------------------------------------------------------------
# FUNCTION: apply_conditions(item, conditions, verbose=False, extra_verbose=False)
#  PURPOSE: to evaluate conditions on data entries
# --------------------------------------------------------------------------
def apply_conditions(item, conditions, verbose=False, extra_verbose=False):
    try:
        if extra_verbose:
            print(f"Evaluating expression tokens: {conditions}")

        result = evaluate_expression(item, conditions, verbose, extra_verbose)

        if verbose:
            print(f"Item {item.get('index', '')} - Condition result: {result}")

        return result
    except Exception as e:
        if verbose or extra_verbose:
            print(f"Error evaluating conditions on item {item}: {e}")
        return False

# --------------------------------------------------------------------------
# FUNCTION: evaluate_expression(item, tokens, verbose=False, extra_verbose=False)
#  PURPOSE: to evaluate a logical expression recursively
# --------------------------------------------------------------------------
def evaluate_expression(item, tokens, verbose=False, extra_verbose=False):
    if len(tokens) == 1:
        result = tokens[0](item)
        if extra_verbose:
            print(f"Result: {result}")
        return result

    for idx, token in enumerate(tokens):
        if token == 'and':
            left = evaluate_expression(item, tokens[:idx], verbose, extra_verbose)
            right = evaluate_expression(item, tokens[idx + 1:], verbose, extra_verbose)
            result = left and right
            if extra_verbose:
                print(f"Evaluating 'and': {left} and {right}")
            return result
        elif token == 'or':
            left = evaluate_expression(item, tokens[:idx], verbose, extra_verbose)
            right = evaluate_expression(item, tokens[idx + 1:], verbose, extra_verbose)
            result = left or right
            if extra_verbose:
                print(f"Evaluating 'or': {left} or {right}")
            return result

# --------------------------------------------------------------------------
# FUNCTION: build_condition_function(condition)
#  PURPOSE: to parse and build a condition function
# --------------------------------------------------------------------------
def build_condition_function(condition):
    match = re.match(r'^\s*(\w+)\s*(!?=)\s*(.*)\s*$', condition)
    if not match:
        raise ValueError(f"Invalid condition format: {condition}")

    field, operator, value = match.groups()
    value = value.strip().strip('"').strip("'")

    if '*' in value or '?' in value:
        return lambda item: fnmatchcase(str(item.get(field, '')), value) if operator == '=' else not fnmatchcase(str(item.get(field, '')), value)
    else:
        if operator == '=':
            return lambda item: str(item.get(field, '')) == value
        elif operator == '!=':
            return lambda item: str(item.get(field, '')) != value
        else:
            raise ValueError(f"Unsupported operator: {operator}")

# --------------------------------------------------------------------------
# FUNCTION: parse_query(query)
#  PURPOSE: to parse a query into evaluable conditions
# --------------------------------------------------------------------------
def parse_query(query):
    tokens = re.split(r'\s+(and|or)\s+', query, flags=re.IGNORECASE)
    return [build_condition_function(token.strip()) if token.lower() not in ['and', 'or'] else token.lower() for token in tokens]

# --------------------------------------------------------------------------
# FUNCTION: from_json(file_path, output="json", query=None, verbose=0)
# --------------------------------------------------------------------------
#  PURPOSE: exposed function to provide the same functionality main(), but
#       primarily to used when included in other scripts as a module
#  USAGE:
#       converters.from_json(file="path/to/file.json", output="table", query="FIELD = value", verbose=1)
# --------------------------------------------------------------------------
def from_json(file_path, output="json", query=None, verbose=0):
    with open(file_path, "r") as file:
        data = json.load(file)

    if query:
        data = filter_data(data, query, verbose=verbose >= 1, extra_verbose=verbose >= 2)

    if output == "json":
        print_json(data)
    elif output == "csv":
        print_csv(data, index_first=True)
    elif output == "table":
        print_table(data, index_first=True)

# ------------------------------------------------------------------------------------
# FUNCTION: main()
#  PURPOSE: Main function to handle argument parsing and call appropriate functions
# ------------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Convert JSON data to various formats.")
    parser.add_argument("-f", "--file", type=str, help="Path to the input JSON file")
    parser.add_argument("-o", "--output", type=str, choices=["json", "csv", "table"], default="json", help="Output format (default: json)")
    parser.add_argument("-q", "--query", type=str, help='FOR CASE SENSITIVE QUERIES LIKE -q "FIELDNAME = value" | -q "IP != 10.* and PORT=8443"')
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Enable verbose mode (-v for condition results, -vv for full evaluation logs)")
    args = parser.parse_args()

    with open(args.file, "r") as file:
        data = json.load(file)

    verbose = args.verbose >= 1
    extra_verbose = args.verbose >= 2

    if args.query:
        data = filter_data(data, args.query, verbose, extra_verbose)

    if args.output == "json":
        print_json(data)
    elif args.output == "csv":
        print_csv(data, index_first=True)
    elif args.output == "table":
        print_table(data, index_first=True)


if __name__ == "__main__":
    main()
