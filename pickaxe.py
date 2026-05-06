#!/usr/bin/env python3
# --------------------------------------------------------------------------
# Script: pickaxe.py
# --------------------------------------------------------------------------
# ABSTRACT: Scans a workspace directory for "tool-worthy" scripts buried
#     inside compound mono-repos or untracked directories. For each candidate
#     it reports the detected version, author, creation/update dates, and
#     git history depth. Outputs a Markdown report of extraction candidates
#     with suggested git-filter-repo commands for preserving history.
#
#     Inspired by years of hoarding useful scripts in the wrong repos.
#     "You don't lose your tools — you just forget where you put them."
#
# CREATED: 26-0506 - BY: wwwizards <github.com/wwwizards>
# UPDATED: 26-0506 - BY: wwwizards <github.com/wwwizards> - initial public release
# VERSION: v0.1.0
# LICENSE: MIT - https://opensource.org/licenses/MIT
# COPYRIGHT: (c) 2026 wwwizards <github.com/wwwizards>
# AUTODOC: https://github.com/wwwizards/pickaxe  # yes, this file documents itself
#
# USAGE:
#     python pickaxe.py [root_dir] [options]
#
# EXAMPLES:
#     python pickaxe.py ~/DATA/projects
#     python pickaxe.py ~/DATA/projects --min-score 2 --output pickaxe-report.md
#     python pickaxe.py ~/DATA/projects --extensions .py .ps1 .sh
# --------------------------------------------------------------------------

import os
import re
import sys
import argparse
import subprocess
import datetime

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

DEFAULT_EXTENSIONS = ['.py', '.ps1', '.sh', '.rb']
SKIP_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    'site-packages', '.collections', '.azure-pipelines',
}

# Header field regexes (match common inline comment header patterns)
RE_VERSION  = re.compile(r'VERSION\s*[:\-=]\s*v?([\d.]+)', re.IGNORECASE)
RE_CREATED  = re.compile(r'CREATED\s*[:\-]\s*([\d\-/]+)', re.IGNORECASE)
RE_UPDATED  = re.compile(r'UPDATED\s*[:\-]\s*([\d\-/]+)', re.IGNORECASE)
RE_AUTHOR   = re.compile(r'(?:AUTHOR|by)[:\s]+([^\n<>]+?)(?:\s*<|\s*$)', re.IGNORECASE)
RE_SHEBANG  = re.compile(r'^#!')
RE_PURPOSE  = re.compile(r'(?:PURPOSE|ABSTRACT|DESCRIPTION)\s*[:\-]\s*(.{10,80})', re.IGNORECASE)
RE_LICENSE  = re.compile(r'LICENSE\s*[:\-]\s*(.+)', re.IGNORECASE)

# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------

def find_git_root(path):
    """Walk up from path until we find a .git directory. Returns None if not found."""
    current = os.path.abspath(path)
    while True:
        if os.path.isdir(os.path.join(current, '.git')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def git_log_count(git_root, file_path):
    """Return the number of commits that touch file_path within git_root."""
    rel = os.path.relpath(file_path, git_root)
    try:
        result = subprocess.check_output(
            ['git', '-C', git_root, 'log', '--follow', '--oneline', '--', rel],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        lines = [l for l in result.splitlines() if l]
        return len(lines), lines[:5]   # count + first 5 commits
    except Exception:
        return 0, []


def git_filter_repo_cmd(git_root, file_path):
    """Suggest a git-filter-repo command to extract this file's history."""
    rel = os.path.relpath(file_path, git_root)
    return (
        f"  # Clone first: git clone {git_root} /tmp/extracted-repo\n"
        f"  git -C /tmp/extracted-repo filter-repo --path '{rel}' --force"
    )


def parse_header(file_path, max_lines=60):
    """Read up to max_lines of a file and extract metadata from the header block."""
    meta = {
        'shebang': False,
        'version': None,
        'created': None,
        'updated': None,
        'author': None,
        'purpose': None,
        'license': None,
    }
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f):
                if i == 0 and RE_SHEBANG.match(line):
                    meta['shebang'] = True
                if i >= max_lines:
                    break
                if not meta['version']  and RE_VERSION.search(line):
                    meta['version']  = RE_VERSION.search(line).group(1)
                if not meta['created']  and RE_CREATED.search(line):
                    meta['created']  = RE_CREATED.search(line).group(1).strip()
                if not meta['updated']  and RE_UPDATED.search(line):
                    meta['updated']  = RE_UPDATED.search(line).group(1).strip()
                if not meta['author']   and RE_AUTHOR.search(line):
                    meta['author']   = RE_AUTHOR.search(line).group(1).strip()
                if not meta['purpose']  and RE_PURPOSE.search(line):
                    meta['purpose']  = RE_PURPOSE.search(line).group(1).strip()
                if not meta['license']  and RE_LICENSE.search(line):
                    meta['license']  = RE_LICENSE.search(line).group(1).strip()
    except Exception:
        pass
    return meta


def score_candidate(meta, git_commits):
    """
    Score how "tool-worthy" a file is for extraction.
    Higher = better candidate.

      +1  has shebang
      +2  has VERSION header
      +1  has CREATED date
      +1  has PURPOSE/ABSTRACT
      +1  has LICENSE
      +1  has <= 3 git commits (mono-repo squatter)
      +0  has > 10 git commits (belongs where it is)
    """
    s = 0
    if meta['shebang']:   s += 1
    if meta['version']:   s += 2
    if meta['created']:   s += 1
    if meta['purpose']:   s += 1
    if meta['license']:   s += 1
    if 0 < git_commits <= 3:  s += 1
    return s


# --------------------------------------------------------------------------
# MAIN SCAN
# --------------------------------------------------------------------------

def scan(root, extensions, min_score):
    root = os.path.abspath(root)
    candidates = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            fpath = os.path.join(dirpath, fname)
            meta = parse_header(fpath)

            git_root = find_git_root(dirpath)
            commit_count = 0
            recent_commits = []
            if git_root:
                commit_count, recent_commits = git_log_count(git_root, fpath)

            score = score_candidate(meta, commit_count)
            if score < min_score:
                continue

            candidates.append({
                'path':           fpath,
                'rel':            os.path.relpath(fpath, root),
                'score':          score,
                'git_root':       git_root,
                'commits':        commit_count,
                'recent_commits': recent_commits,
                'meta':           meta,
            })

    # Sort by score desc, then path
    candidates.sort(key=lambda c: (-c['score'], c['rel']))
    return candidates


# --------------------------------------------------------------------------
# OUTPUT
# --------------------------------------------------------------------------

def render_markdown(candidates, root, args):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        f"# pickaxe report",
        f"",
        f"**Scanned:** `{root}`  ",
        f"**Date:** {now}  ",
        f"**Min score:** {args.min_score}  ",
        f"**Extensions:** {', '.join(args.extensions)}  ",
        f"**Candidates found:** {len(candidates)}",
        f"",
        f"---",
        f"",
    ]

    for c in candidates:
        m = c['meta']
        in_git = f"`{os.path.relpath(c['git_root'], root)}`" if c['git_root'] else "_none (untracked)_"
        lines += [
            f"## `{c['rel']}`",
            f"",
            f"| Field | Value |",
            f"|---|---|",
            f"| **Score** | {c['score']} |",
            f"| **Version** | {m['version'] or '—'} |",
            f"| **Created** | {m['created'] or '—'} |",
            f"| **Updated** | {m['updated'] or '—'} |",
            f"| **Author** | {m['author'] or '—'} |",
            f"| **License** | {m['license'] or '—'} |",
            f"| **Git repo** | {in_git} |",
            f"| **Git commits** | {c['commits']} |",
        ]
        if m['purpose']:
            lines.append(f"| **Purpose** | {m['purpose'][:120]} |")
        lines.append("")

        if c['commits'] > 0 and c['git_root']:
            lines += [
                f"**History worth preserving** ({c['commits']} commits):",
                f"```bash",
                git_filter_repo_cmd(c['git_root'], c['path']),
                f"```",
                "",
            ]
        elif not c['git_root']:
            lines += [
                f"_Not in any git repo — init fresh:_",
                f"```bash",
                f"  mkdir ~/DATA/miners/<repo-name>",
                f"  cp '{c['path']}' ~/DATA/miners/<repo-name>/",
                f"  git -C ~/DATA/miners/<repo-name> init && git add -A && git commit -m 'init'",
                f"```",
                "",
            ]
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def render_table(candidates, root):
    """Compact terminal table output."""
    print(f"\n{'SCORE':>5}  {'COMMITS':>7}  {'VERSION':>8}  {'PATH'}")
    print(f"{'-'*5}  {'-'*7}  {'-'*8}  {'-'*60}")
    for c in candidates:
        ver = c['meta']['version'] or '—'
        print(f"{c['score']:>5}  {c['commits']:>7}  {ver:>8}  {c['rel']}")
    print(f"\n{len(candidates)} candidates found.")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="pickaxe — mine tool-worthy scripts from compound mono-repos"
    )
    parser.add_argument(
        'root', nargs='?', default='.',
        help='Root directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--min-score', '-s', type=int, default=3,
        help='Minimum score to include in report (default: 3)'
    )
    parser.add_argument(
        '--extensions', '-e', nargs='+', default=DEFAULT_EXTENSIONS,
        help=f'File extensions to scan (default: {DEFAULT_EXTENSIONS})'
    )
    parser.add_argument(
        '--output', '-o', default=None,
        help='Write Markdown report to this file (default: print table to stdout)'
    )
    parser.add_argument(
        '--all', '-a', action='store_true',
        help='Include all candidates regardless of score'
    )
    args = parser.parse_args()

    if args.all:
        args.min_score = 0

    print(f"[pickaxe] scanning {os.path.abspath(args.root)} ...", file=sys.stderr)
    candidates = scan(args.root, args.extensions, args.min_score)

    if args.output:
        md = render_markdown(candidates, os.path.abspath(args.root), args)
        with open(args.output, 'w') as f:
            f.write(md)
        print(f"[pickaxe] report written to {args.output}", file=sys.stderr)
    else:
        render_table(candidates, os.path.abspath(args.root))


if __name__ == '__main__':
    main()
