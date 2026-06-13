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
# UPDATED: 26-0527 - BY: wwwizards <github.com/wwwizards> - --save on scan; _build_scan_summary; session trajectory support
# UPDATED: 26-0603 - BY: wwwizards <github.com/wwwizards> - gitlink submodule support (_resolve_git_dir; find_git_root; diagnose; discover)
# VERSION: v0.3.2
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
#     python pickaxe.py ~/DATA/projects --dry-run --output extraction-plan.md
# --------------------------------------------------------------------------

import os
import re
import sys
import json
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
    """Walk up from path until we find a .git dir or gitlink file. Returns None if not found."""
    current = os.path.abspath(path)
    while True:
        git_marker = os.path.join(current, '.git')
        if os.path.isdir(git_marker) or os.path.isfile(git_marker):
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


# --------------------------------------------------------------------------
# DIAGNOSE / DISCOVER  (5D phase 1 & 2)
# --------------------------------------------------------------------------

def _resolve_git_dir(path):
    """
    Return the actual git directory for a repo rooted at path.

    Handles two cases:
      - Normal repo:          path/.git  is a directory  → return it as-is
      - Submodule worktree:   path/.git  is a gitlink file
                              (content: "gitdir: <rel-or-abs-path>")
                              → resolve and return the real store dir

    Returns None if no .git marker exists at all.
    """
    git_marker = os.path.join(path, '.git')
    if os.path.isdir(git_marker):
        return git_marker
    if os.path.isfile(git_marker):
        try:
            line = open(git_marker, encoding='utf-8').read().strip()
            if line.startswith('gitdir:'):
                rel = line[len('gitdir:'):].strip()
                return os.path.normpath(os.path.join(path, rel))
        except Exception:
            pass
    return None


def _get_branch(path):
    """Read current branch name from .git/HEAD. Returns None if unreadable."""
    git_dir = _resolve_git_dir(path)
    if git_dir is None:
        return None
    head_path = os.path.join(git_dir, 'HEAD')
    if not os.path.isfile(head_path):
        return None
    try:
        content = open(head_path, encoding='utf-8').read().strip()
        if content.startswith('ref: refs/heads/'):
            return content[len('ref: refs/heads/'):]
        return content[:8]  # detached HEAD — return short hash
    except Exception:
        return None


def diagnose(path):
    """
    Inspect repo health at path (Diagnose phase — read-only).
    Returns a dict with keys: path, has_git, has_origin, remote_url, flags.
    Flags: 'ok' | 'submodule' | 'missing_git' | 'missing_origin' | 'stripped_config'

    Handles both normal repos (.git is a directory) and submodule worktrees
    (.git is a gitlink file like "gitdir: ../../../../.git/modules/foo").
    Never mutates anything.
    """
    path = os.path.abspath(path)
    result = {
        'path': path,
        'has_git': False,
        'has_origin': False,
        'remote_url': None,
        'flags': [],
    }

    git_marker = os.path.join(path, '.git')
    is_submodule = os.path.isfile(git_marker)  # gitlink file = submodule worktree
    git_dir = _resolve_git_dir(path)

    if git_dir is None:
        result['flags'].append('missing_git')
        return result

    result['has_git'] = True
    if is_submodule:
        result['flags'].append('submodule')

    config_path = os.path.join(git_dir, 'config')
    if not os.path.isfile(config_path):
        result['flags'].append('stripped_config')
        return result

    try:
        content = open(config_path, encoding='utf-8').read()
    except Exception:
        result['flags'].append('stripped_config')
        return result

    if '[remote "origin"]' in content:
        result['has_origin'] = True
        url_match = re.search(r'url\s*=\s*(.+)', content)
        if url_match:
            result['remote_url'] = url_match.group(1).strip()
    else:
        result['flags'].append('missing_origin')

    if not result['flags']:
        result['flags'].append('ok')
    return result


def discover(root):
    """
    Walk root for git repo roots (Discover phase — read-only).
    Returns a list of repo entry dicts:
      {path, rel, remote, branch, flags, health_ok}
    Never mutates anything.
    """
    root = os.path.abspath(root)
    entries = []
    for dirpath, dirnames, _filenames in os.walk(root):
        # Prune dirs we never want to recurse into
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        # Check whether this dir is a git repo root (dir = normal, file = submodule gitlink)
        git_marker = os.path.join(dirpath, '.git')
        if os.path.isdir(git_marker) or os.path.isfile(git_marker):
            health = diagnose(dirpath)
            rel = os.path.relpath(dirpath, root)
            entries.append({
                'path': dirpath,
                'rel': rel,
                'remote': health['remote_url'],
                'branch': _get_branch(dirpath),
                'flags': health['flags'],
                # healthy = has git + has origin; 'submodule' flag is informational, not a failure
                'health_ok': health['has_git'] and health['has_origin'],
            })
            # Remove .git from traversal but keep other subdirs
            # so nested repos (e.g. pickaxe inside LogicWizards) are found
            if '.git' in dirnames:
                dirnames.remove('.git')
    return entries


def extraction_script(git_root, file_path):
    """
    # --------------------------------------------------------------------------
    # FUNCTION: extraction_script
    # --------------------------------------------------------------------------
    # ABSTRACT: Return a complete copy-pasteable extraction pipeline for one file.
    #     Emits a fully-runnable bash script: clone → filter-repo → optionally push.
    # RETURNS:  str
    # --------------------------------------------------------------------------
    """
    rel = os.path.relpath(file_path, git_root)
    stem = os.path.splitext(os.path.basename(file_path))[0]
    dest_name = stem.lower().replace('_', '-')
    lines = [
        f'# --- extraction pipeline: {rel} ---',
        f'DEST_NAME="{dest_name}"  # rename as needed',
        f'SOURCE_REPO="{git_root}"',
        f'CLONE_TMP="/tmp/pickaxe-extract-${{DEST_NAME}}"',
        f'',
        f'# 1. Clone source repo (filter-repo requires a fresh clone)',
        f'git clone "$SOURCE_REPO" "$CLONE_TMP"',
        f'',
        f'# 2. Extract with full history',
        f"git -C \"$CLONE_TMP\" filter-repo --path '{rel}' --force",
        f'',
        f'# 3. Move to destination (or re-clone for a clean working copy)',
        f'mv "$CLONE_TMP" ~/DATA/miners/"$DEST_NAME"',
        f'# Alternative: git clone "$CLONE_TMP" ~/DATA/miners/"$DEST_NAME" && rm -rf "$CLONE_TMP"',
        f'',
        f'# 4. Create remote + push (requires gh CLI; uncomment when ready)',
        f'# cd ~/DATA/miners/"$DEST_NAME"',
        f'# gh repo create wwwizards/"$DEST_NAME" --private --source=. --push',
    ]
    return '\n'.join(lines)


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
    dry_run = getattr(args, 'dry_run', False)
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
            if dry_run:
                lines += [
                    f"**Extraction pipeline** ({c['commits']} commits):",
                    f"```bash",
                    extraction_script(c['git_root'], c['path']),
                    f"```",
                    "",
                ]
            else:
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


def render_table(candidates, root, dry_run=False):
    """Compact terminal table output."""
    print(f"\n{'SCORE':>5}  {'COMMITS':>7}  {'VERSION':>8}  {'PATH'}")
    print(f"{'-'*5}  {'-'*7}  {'-'*8}  {'-'*60}")
    for c in candidates:
        ver = c['meta']['version'] or '—'
        print(f"{c['score']:>5}  {c['commits']:>7}  {ver:>8}  {c['rel']}")
    print(f"\n{len(candidates)} candidates found.")
    if dry_run:
        print()
        for c in candidates:
            if c['commits'] > 0 and c['git_root']:
                print(f"{'='*60}")
                print(f"# {c['rel']}  (score={c['score']}, commits={c['commits']})")
                print(f"{'='*60}")
                print(extraction_script(c['git_root'], c['path']))
                print()


# --------------------------------------------------------------------------
# SESSION LOGGING  (.pickaxe/SESSIONS/)
# --------------------------------------------------------------------------

def _build_discover_summary(entries):
    """Summarise discover results into a compact session-log dict."""
    from collections import Counter
    flag_counts = Counter()
    for e in entries:
        for f in e['flags']:
            if f != 'ok':
                flag_counts[f] += 1
    return {
        'repos_found': len(entries),
        'health_ok':   sum(1 for e in entries if e['health_ok']),
        'flag_counts': dict(flag_counts),
    }


def _build_diagnose_summary(result):
    """Summarise diagnose result into a compact session-log dict."""
    return {
        'has_git':    result['has_git'],
        'has_origin': result['has_origin'],
        'flags':      result['flags'],
    }


def _build_scan_summary(candidates, root):
    """Summarise scan results into a compact session-log dict."""
    from collections import Counter
    score_dist = Counter(c['score'] for c in candidates)
    return {
        'candidates_found': len(candidates),
        'score_distribution': dict(sorted(score_dist.items())),
        'top_score': max((c['score'] for c in candidates), default=0),
        'root': os.path.relpath(root, root),  # always '.' — sentinel for portability
    }


def _save_session_event(phase, target_abs, result_summary, sessions_dir):
    """
    Append a 5D event record (NDJSON) to .pickaxe/SESSIONS/YYMMDD-<topic>.json.

    target_abs   : absolute path that was scanned / diagnosed
    sessions_dir : .pickaxe/SESSIONS/ absolute path in the managed workspace

    The 'target' field is stored as a forward-slash relative path so session
    logs survive machine migrations and cross-platform replays.
    """
    os.makedirs(sessions_dir, exist_ok=True)

    workspace_root = os.path.dirname(os.path.dirname(sessions_dir))  # .pickaxe/../
    try:
        rel_target = os.path.relpath(target_abs, workspace_root).replace('\\', '/')
    except ValueError:
        rel_target = target_abs.replace('\\', '/')  # different drive on Windows

    ts_iso   = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    date_pfx = datetime.datetime.now().strftime('%y%m%d')
    topic    = os.path.basename(target_abs.rstrip('/\\')) or 'root'
    filepath = os.path.join(sessions_dir, f"{date_pfx}-{topic}.json")

    event = {
        'ts':     ts_iso,
        'phase':  phase,
        'target': rel_target,
        'result': result_summary,
    }
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event) + '\n')
    return filepath


# --------------------------------------------------------------------------
# OUTPUT — discover / diagnose
# --------------------------------------------------------------------------

def render_discover_table(entries):
    """Print a compact table of discovered repos."""
    print(f"\n{'HEALTH':>7}  {'BRANCH':>10}  {'FLAGS':>20}  PATH")
    print(f"{'-'*7}  {'-'*10}  {'-'*20}  {'-'*60}")
    for e in entries:
        health = 'ok' if e['health_ok'] else 'WARN'
        branch = e['branch'] or '—'
        flags  = ','.join(e['flags'])
        print(f"{health:>7}  {branch:>10}  {flags:>20}  {e['rel']}")
    print(f"\n{len(entries)} repo(s) found.")


def render_diagnose_table(result):
    """Print a single-repo diagnose result."""
    status = 'ok' if 'ok' in result['flags'] else 'WARN'
    print(f"\n[{status}] {result['path']}")
    print(f"  has_git   : {result['has_git']}")
    print(f"  has_origin: {result['has_origin']}")
    print(f"  remote_url: {result['remote_url'] or '—'}")
    print(f"  flags     : {', '.join(result['flags'])}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _cmd_discover(args):
    root = os.path.abspath(getattr(args, 'root_dir', None) or args.root or '.')
    print(f"[pickaxe discover] scanning {root} ...", file=sys.stderr)
    entries = discover(root)
    if args.format == 'json':
        print(json.dumps(entries, indent=2))
    else:
        render_discover_table(entries)
    if args.save:
        sessions_dir = os.path.join(root, '.pickaxe', 'SESSIONS')
        saved = _save_session_event('discover', root, _build_discover_summary(entries), sessions_dir)
        print(f"[pickaxe] session event saved → {saved}", file=sys.stderr)


def _cmd_diagnose(args):
    path = os.path.abspath(args.path or '.')
    print(f"[pickaxe diagnose] {path}", file=sys.stderr)
    result = diagnose(path)
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        render_diagnose_table(result)
    if args.save:
        sessions_dir = os.path.join(path, '.pickaxe', 'SESSIONS')
        saved = _save_session_event('diagnose', path, _build_diagnose_summary(result), sessions_dir)
        print(f"[pickaxe] session event saved → {saved}", file=sys.stderr)


def _cmd_scan(args):
    """Legacy scan behaviour (Discover phase — extraction candidates)."""
    if args.all:
        args.min_score = 0
    root_abs = os.path.abspath(args.root)
    print(f"[pickaxe] scanning {root_abs} ...", file=sys.stderr)
    candidates = scan(args.root, args.extensions, args.min_score)
    fmt = getattr(args, 'format', 'table')
    if fmt == 'json':
        # Emit JSON-serialisable subset (drop non-serialisable meta internals)
        out = [{
            'rel':     c['rel'],
            'score':   c['score'],
            'commits': c['commits'],
            'version': c['meta'].get('version'),
            'created': c['meta'].get('created'),
            'author':  c['meta'].get('author'),
            'license': c['meta'].get('license'),
            'purpose': c['meta'].get('purpose'),
        } for c in candidates]
        print(json.dumps(out, indent=2))
    elif args.output:
        md = render_markdown(candidates, root_abs, args)
        with open(args.output, 'w') as f:
            f.write(md)
        print(f"[pickaxe] report written to {args.output}", file=sys.stderr)
    else:
        render_table(candidates, root_abs, dry_run=args.dry_run)
    if args.save:
        sessions_dir = os.path.join(root_abs, '.pickaxe', 'SESSIONS')
        saved = _save_session_event('scan', root_abs, _build_scan_summary(candidates, root_abs), sessions_dir)
        print(f"[pickaxe] session event saved → {saved}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="pickaxe — 5D repo health + extraction tool (wwwizards)"
    )
    sub = parser.add_subparsers(dest='command', metavar='command')

    # --- discover ---
    p_discover = sub.add_parser(
        'discover', help='Emit local repo map (path, remote, branch, health flags)'
    )
    p_discover.add_argument('root_dir', nargs='?', default='.', metavar='root', help='Root dir to walk')
    p_discover.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_discover.add_argument('--save', action='store_true',
                             help='Append session event to {root}/.pickaxe/SESSIONS/')
    p_discover.set_defaults(func=_cmd_discover)

    # --- diagnose ---
    p_diagnose = sub.add_parser(
        'diagnose', help='Inspect repo health (missing .git, origin, config)'
    )
    p_diagnose.add_argument('path', nargs='?', default='.', help='Repo path to inspect')
    p_diagnose.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_diagnose.add_argument('--save', action='store_true',
                             help='Append session event to {path}/.pickaxe/SESSIONS/')
    p_diagnose.set_defaults(func=_cmd_diagnose)

    # --- scan ---
    p_scan = sub.add_parser(
        'scan', help='Score files as extraction candidates (version, commits, headers)'
    )
    p_scan.add_argument('root', nargs='?', default='.', help='Root dir to scan')
    p_scan.add_argument('--min-score', '-s', type=int, default=3)
    p_scan.add_argument('--extensions', '-e', nargs='+', default=DEFAULT_EXTENSIONS)
    p_scan.add_argument('--output', '-o', default=None)
    p_scan.add_argument('--all', '-a', action='store_true')
    p_scan.add_argument('--dry-run', '-d', action='store_true')
    p_scan.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_scan.add_argument('--save', action='store_true',
                         help='Append session event to {root}/.pickaxe/SESSIONS/')
    p_scan.set_defaults(func=_cmd_scan)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
