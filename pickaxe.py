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
# UPDATED: 26-0614 - BY: wwwizards <github.com/wwwizards> - commit_trends (discover commit-trends; --by week|day|month; --from/--to; --marathon-threshold; --holidays)
# UPDATED: 26-0614 - BY: wwwizards <github.com/wwwizards> - scan: already-extracted annotation (PX-B3); discover --submodules-only (PX-B1)
# UPDATED: 26-0721 - BY: wwwizards <github.com/wwwizards> - backup/restore (PX-B4): bundle+working-tree snapshot; manifest.json; restore from bundle
# UPDATED: 26-0721 - BY: wwwizards <github.com/wwwizards> - discover drift (PX-D1): fetch + ahead/behind/dirty per repo; _render_drift_table
# UPDATED: 26-0729 - BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - diagnose instruction-bloat (A1/A3, noun-dispatch retrofit); deliver instruction-rollup (A2/A4, first-ever deliver verb)
# UPDATED: 26-0729 - BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - fix LB-03: instruction-rollup snapshot-before-mutate + overlap skip (execute/plan_instruction_rollup)
# UPDATED: 26-0729 - BY: Claude(Sonnet5)::WIZ-00.Copilot::pickaxe.SOLOMON - fix LB-04: .github/ sources extract to .github/instructions/ (VS Code auto-discovery); pointer links now source-dir-relative
# VERSION: v0.4.2
# LICENSE: MIT - https://opensource.org/licenses/MIT
# COPYRIGHT: (c) 2026 wwwizards <github.com/wwwizards>
# AUTODOC: https://github.com/wwwizards/pickaxe  # yes, this file documents itself
#
# USAGE:
#     python pickaxe.py <command> [options]
#
# COMMANDS:
#     scan      Score files as extraction candidates (version, commits, headers)
#     discover  Repo health map | commit-trends | drift
#     diagnose  Single-repo health inspection | instruction-bloat
#     deliver   instruction-rollup (dry-run by default, --execute to write)
#     backup    Snapshot all repos (git bundles + working-tree) to a portable dir
#     restore   Restore repos from a pickaxe backup manifest
#
# EXAMPLES — scan:
#     python pickaxe.py scan ~/DATA/projects
#     python pickaxe.py scan ~/DATA/projects --min-score 2 --output report.md
#     python pickaxe.py scan ~/DATA/projects --extensions .py .ps1 .sh
#
# EXAMPLES — discover / diagnose:
#     python pickaxe.py discover ~/DATA/projects
#     python pickaxe.py discover commit-trends --by week
#     python pickaxe.py diagnose ~/DATA/projects/my-tool
#     python pickaxe.py diagnose instruction-bloat ~/DATA/projects --format json --save
#
# EXAMPLES — deliver:
#     python pickaxe.py diagnose instruction-bloat . --format json > findings.json
#     python pickaxe.py deliver instruction-rollup . --from-report findings.json
#     python pickaxe.py deliver instruction-rollup . --from-report findings.json --execute
#
# EXAMPLES — backup / restore:
#     python pickaxe.py backup ~/DATA/projects --to ~/backups/LW-260721
#     python pickaxe.py backup ~/DATA/projects --to ~/backups/LW-260721 --skip-working-tree
#     python pickaxe.py backup . --to ~/backups/LW-260721 --format json
#     python pickaxe.py restore ~/backups/LW-260721 --to ~/restored
#     python pickaxe.py restore ~/backups/LW-260721 --to ~/restored --format json
# --------------------------------------------------------------------------

import os
import re
import sys
import json
import shutil
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


def _get_remote_url(path):
    """Return the 'origin' remote URL for the git repo at path, or None."""
    try:
        result = subprocess.run(
            ['git', '-C', path, 'remote', 'get-url', 'origin'],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
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


def discover_remote_drift(root):
    """
    Walk root for git repos, fetch each origin, and measure ahead/behind/dirty.
    Returns list of dicts: {rel, path, remote, branch, ahead, behind, dirty, flags}
    Repos without a remote are included with flags=['no-remote'].
    flags may include: push-needed, behind, uncommitted, no-remote, fetch-failed
    """
    repos = discover(root)
    results = []
    for repo in repos:
        path   = repo['path']
        rel    = repo['rel']
        remote = repo.get('remote') or ''
        branch = repo.get('branch') or 'main'

        entry = {
            'rel':    rel,
            'path':   path,
            'remote': remote,
            'branch': branch,
            'ahead':  0,
            'behind': 0,
            'dirty':  0,
            'flags':  [],
        }

        if not remote:
            entry['flags'].append('no-remote')
            results.append(entry)
            continue

        fetch = subprocess.run(
            ['git', '-C', path, 'fetch', 'origin', '--quiet'],
            capture_output=True, text=True)
        if fetch.returncode != 0:
            entry['flags'].append('fetch-failed')
            results.append(entry)
            continue

        def _count(cmd):
            r = subprocess.run(cmd, capture_output=True, text=True)
            return len([ln for ln in r.stdout.splitlines() if ln]) if r.returncode == 0 else 0

        ahead  = _count(['git', '-C', path, 'log', f'origin/{branch}..HEAD', '--oneline'])
        behind = _count(['git', '-C', path, 'log', f'HEAD..origin/{branch}', '--oneline'])
        dirty  = _count(['git', '-C', path, 'status', '--porcelain'])

        entry['ahead']  = ahead
        entry['behind'] = behind
        entry['dirty']  = dirty

        if ahead  > 0: entry['flags'].append('push-needed')
        if behind > 0: entry['flags'].append('behind')
        if dirty  > 0 and ahead == 0 and behind == 0:
            entry['flags'].append('uncommitted')

        results.append(entry)

    return results


# --------------------------------------------------------------------------
# DIAGNOSE INSTRUCTION-BLOAT  (diagnose instruction-bloat — A1/A3, read-only)
# --------------------------------------------------------------------------

DIAGNOSE_NOUNS = {'instruction-bloat'}

_INSTRUCTION_FILE_EXACT = {'AGENTS.md', 'SKILL.md', 'copilot-instructions.md'}
_INSTRUCTION_FILE_SUFFIX = '.instructions.md'
_HEADING_RE = re.compile(r'^(#{2,3})\s+(.+?)\s*$')


def _is_instruction_file(path):
    """True if path's basename matches a tracked instruction-file convention."""
    base = os.path.basename(path)
    return base in _INSTRUCTION_FILE_EXACT or base.endswith(_INSTRUCTION_FILE_SUFFIX)


def _find_instruction_files(root):
    """
    Walk root for tracked instruction files (read-only). Reuses SKIP_DIRS so
    nested submodule .github/ dirs are still found (the walk doesn't stop at
    repo boundaries, same as discover()/scan()).
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            if _is_instruction_file(full):
                found.append(full)
    return found


def _parse_sections(lines):
    """
    Split a Markdown file's lines into ## / ### sections.
    Returns a list of {heading, start_line, end_line} (1-indexed, inclusive).
    Content before the first heading is not returned as a section.
    """
    sections = []
    current = None
    for i, line in enumerate(lines, start=1):
        m = _HEADING_RE.match(line)
        if m:
            if current is not None:
                current['end_line'] = i - 1
                sections.append(current)
            current = {'heading': m.group(2).strip(), 'start_line': i, 'end_line': None}
    if current is not None:
        current['end_line'] = len(lines)
        sections.append(current)
    return sections


def diagnose_instruction_bloat(root, max_lines=1000, max_section_lines=50):
    """
    Diagnose phase (read-only): scan root for instruction files and flag
    whole-file line-count bloat and per-section (>max_section_lines) scatter,
    per the triggers already documented in root copilot-instructions.md.

    Returns a list of finding dicts:
      {file, start_line, end_line, reason, kind, heading}
    kind is 'whole-file' | 'section'. file is relative to root. Never mutates.
    This is the diagnose->deliver handoff schema consumed by
    `deliver instruction-rollup --from-report`.
    """
    root = os.path.abspath(root)
    findings = []
    for path in _find_instruction_files(root):
        try:
            with open(path, encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            continue
        total = len(lines)
        rel = os.path.relpath(path, root).replace(os.sep, '/')

        if total > max_lines:
            findings.append({
                'file': rel,
                'start_line': 1,
                'end_line': total,
                'reason': f'whole-file line count {total} exceeds --max-lines {max_lines}',
                'kind': 'whole-file',
                'heading': None,
            })

        for section in _parse_sections(lines):
            span = section['end_line'] - section['start_line'] + 1
            if span > max_section_lines:
                findings.append({
                    'file': rel,
                    'start_line': section['start_line'],
                    'end_line': section['end_line'],
                    'reason': (f"section '{section['heading']}' spans {span} lines, "
                               f"exceeds --max-section-lines {max_section_lines}"),
                    'kind': 'section',
                    'heading': section['heading'],
                })
    return findings


# --------------------------------------------------------------------------
# DELIVER INSTRUCTION-ROLLUP  (deliver instruction-rollup — A2/A4, mutating)
# --------------------------------------------------------------------------

DELIVER_NOUNS = {'instruction-rollup'}

_ROLLUP_FRONTMATTER = """---
description: {description}
applyTo: '**'  # TODO: narrow this glob — auto-fill cannot infer scope
requires:
  - '.github/copilot-instructions.md'
version: 0.1.0
tags: []  # TODO: fill in relevant keywords
status: experimental
lastModified: {date}
maintainer: TBD  # TODO: assign an owner
---

"""


def _slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug or 'rollup'


def _rollup_dest_path(source_abs, finding):
    """
    Destination for an extracted finding. Sources that live directly in a
    `.github/` directory route into `.github/instructions/` — the directory
    VS Code's Copilot instructions-file auto-discovery actually scans for
    `applyTo`-scoped files. A `.instructions.md` file dropped loose in
    `.github/` (sibling to copilot-instructions.md) is not auto-discovered
    and would silently orphan the extracted content. Other source locations
    keep same-directory placement (not subject to that auto-discovery rule).
    """
    heading = finding.get('heading')
    slug = _slugify(heading) if heading else f"rollup-{finding['start_line']}-{finding['end_line']}"
    source_dir = os.path.dirname(source_abs)
    if os.path.basename(source_dir) == '.github':
        source_dir = os.path.join(source_dir, 'instructions')
    return os.path.join(source_dir, f'{slug}.instructions.md')


def plan_instruction_rollup(findings, root):
    """
    Discover phase for deliver — compute the plan without touching disk.
    Returns list of {file, dest, start_line, end_line, heading, status}.
    status: 'planned' | 'already_extracted' | 'skipped_overlap'

    'skipped_overlap' mirrors execute_instruction_rollup's LB-03 fix: a
    section finding fully contained within a whole-file finding's range
    for the same source is never extracted on its own (its text already
    lives in the whole-file dump) — the plan must say so up front rather
    than claim 'planned' for a range execute will silently skip.
    """
    root = os.path.abspath(root)

    by_file = {}
    for finding in findings:
        by_file.setdefault(finding['file'], []).append(finding)

    plans = []
    for file_rel, file_findings in by_file.items():
        whole_file_ranges = [
            (f['start_line'], f['end_line']) for f in file_findings if f['kind'] == 'whole-file'
        ]

        def _contained_in_whole_file(finding):
            return any(
                s <= finding['start_line'] and finding['end_line'] <= e
                for s, e in whole_file_ranges
            )

        for finding in file_findings:
            source_abs = os.path.join(root, finding['file'])
            dest_abs = _rollup_dest_path(source_abs, finding)
            dest_rel = os.path.relpath(dest_abs, root).replace(os.sep, '/')

            if os.path.isfile(dest_abs):
                status = 'already_extracted'
            elif finding['kind'] != 'whole-file' and _contained_in_whole_file(finding):
                status = 'skipped_overlap'
            else:
                status = 'planned'

            plans.append({
                'file': finding['file'],
                'dest': dest_rel,
                'start_line': finding['start_line'],
                'end_line': finding['end_line'],
                'heading': finding.get('heading'),
                'status': status,
            })
    return plans


def execute_instruction_rollup(findings, root):
    """
    Deliver phase — mutating. Extracts each finding's line range into a new
    scoped `*.instructions.md` file (Instruction Inheritance Pattern
    frontmatter, auto-filled where possible) and leaves a pointer line in the
    source. Idempotent: skips any finding whose destination file already
    exists (repo's own Idempotent Script Pattern rule).

    LB-03 fix: findings are grouped by source file and read from a single
    pristine snapshot, never re-read from disk mid-loop — a prior version
    re-opened the source after each write, so every extraction after the
    first read the already-mutated (pointer-stubbed) file and silently wrote
    empty bodies. Any section finding fully contained within a whole-file
    finding's range is skipped (its text already lives in the whole-file
    dump); remaining ranges are replaced with pointers back-to-front against
    the snapshot so earlier line numbers never shift under later writes.

    Returns list of {file, dest, status} where status is
    'extracted' | 'already_extracted' | 'skipped_overlap' | 'error: <msg>'.
    """
    root = os.path.abspath(root)
    results = []

    by_file = {}
    for finding in findings:
        by_file.setdefault(finding['file'], []).append(finding)

    for file_rel, file_findings in by_file.items():
        source_abs = os.path.join(root, file_rel)
        try:
            with open(source_abs, encoding='utf-8') as f:
                original_lines = f.readlines()
        except Exception as exc:
            for finding in file_findings:
                dest_abs = _rollup_dest_path(source_abs, finding)
                dest_rel = os.path.relpath(dest_abs, root).replace(os.sep, '/')
                results.append({'file': finding['file'], 'dest': dest_rel, 'status': f'error: {exc}'})
            continue

        whole_file_ranges = [
            (f['start_line'], f['end_line']) for f in file_findings if f['kind'] == 'whole-file'
        ]

        def _contained_in_whole_file(finding):
            return any(
                s <= finding['start_line'] and finding['end_line'] <= e
                for s, e in whole_file_ranges
            )

        applied = []  # (start, end, dest_rel) extracted from this snapshot
        for finding in file_findings:
            dest_abs = _rollup_dest_path(source_abs, finding)
            dest_rel = os.path.relpath(dest_abs, root).replace(os.sep, '/')

            if os.path.isfile(dest_abs):
                results.append({'file': finding['file'], 'dest': dest_rel, 'status': 'already_extracted'})
                continue

            if finding['kind'] != 'whole-file' and _contained_in_whole_file(finding):
                results.append({'file': finding['file'], 'dest': dest_rel, 'status': 'skipped_overlap'})
                continue

            start, end = finding['start_line'], finding['end_line']
            extracted = original_lines[start - 1:end]
            heading = finding.get('heading') or os.path.splitext(os.path.basename(dest_abs))[0]
            frontmatter = _ROLLUP_FRONTMATTER.format(
                description=heading,
                date=datetime.date.today().isoformat(),
            )

            os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
            with open(dest_abs, 'w', encoding='utf-8') as f:
                f.write(frontmatter)
                f.writelines(extracted)

            # Link relative to the SOURCE file's own directory, not the
            # workspace root — dest_rel is root-relative and would double up
            # the .github/ prefix when written as a link inside .github/copilot-instructions.md.
            link_rel = os.path.relpath(dest_abs, os.path.dirname(source_abs)).replace(os.sep, '/')
            results.append({'file': finding['file'], 'dest': dest_rel, 'status': 'extracted'})
            applied.append((start, end, link_rel))

        if not applied:
            continue

        # Replace ranges back-to-front so a lower range's line numbers are
        # never invalidated by an earlier write to a higher range.
        applied.sort(key=lambda t: t[0], reverse=True)
        new_lines = list(original_lines)
        for start, end, link_rel in applied:
            pointer = f"> Extracted to [{os.path.basename(link_rel)}]({link_rel}) via `pickaxe deliver instruction-rollup`.\n"
            new_lines[start - 1:end] = [pointer]

        with open(source_abs, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return results


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
    # Determine the git root of the scan root itself so we can detect
    # candidates that already live in their own separate repo (submodules,
    # externally-cloned directories, etc.) and annotate them rather than
    # silently suggesting re-extraction.
    scan_git_root = find_git_root(root)
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

            # Detect already-extracted: file lives in a different git repo than
            # the scan root.  Retrieve that repo's remote for the annotation.
            already_extracted = None
            if git_root and scan_git_root and os.path.abspath(git_root) != os.path.abspath(scan_git_root):
                remote = _get_remote_url(git_root)
                already_extracted = remote or git_root

            candidates.append({
                'path':             fpath,
                'rel':              os.path.relpath(fpath, root),
                'score':            score,
                'git_root':         git_root,
                'commits':          commit_count,
                'recent_commits':   recent_commits,
                'meta':             meta,
                'already_extracted': already_extracted,
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
    print(f"\n{'SCORE':>5}  {'COMMITS':>7}  {'VERSION':>8}  {'NOTE':>26}  PATH")
    print(f"{'-'*5}  {'-'*7}  {'-'*8}  {'-'*26}  {'-'*60}")
    for c in candidates:
        ver = c['meta']['version'] or '—'
        if c.get('already_extracted'):
            note = f'[extracted → {c["already_extracted"][:22]}]'
        else:
            note = ''
        print(f"{c['score']:>5}  {c['commits']:>7}  {ver:>8}  {note:>26}  {c['rel']}")
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
# COMMIT TRENDS  (discover commit-trends)
# --------------------------------------------------------------------------

DISCOVER_NOUNS = {'commit-trends', 'drift'}


def commit_trends(repo_path, by='week', from_date=None, to_date=None):
    """
    Return commit cadence data for a git repo.

    Parameters
    ----------
    repo_path  : str   Path to any directory inside (or at root of) the repo.
    by         : str   Granularity: 'week' | 'day' | 'month'
    from_date  : str   ISO date string 'YYYY-MM-DD' (inclusive lower bound) or None
    to_date    : str   ISO date string 'YYYY-MM-DD' (inclusive upper bound) or None

    Returns
    -------
    list of {'period': str, 'count': int}
    Sorted chronologically. Empty list if repo has no commits or path is not a repo.
    """
    from collections import Counter

    date_fmt = {
        'week':  '%G-W%V',   # ISO week: 2026-W24
        'day':   '%Y-%m-%d', # 2026-06-14
        'month': '%Y-%m',    # 2026-06
    }.get(by, '%G-W%V')

    repo_path = os.path.abspath(repo_path)
    git_root = find_git_root(repo_path)
    if git_root is None:
        return []

    cmd = [
        'git', '-C', git_root,
        'log',
        f'--format=%ad',
        f'--date=format:{date_fmt}',
    ]
    if from_date:
        cmd += [f'--after={from_date}']
    if to_date:
        cmd += [f'--before={to_date}']

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError:
        return []

    if not output:
        return []

    counts = Counter(line.strip() for line in output.splitlines() if line.strip())
    periods = sorted(counts.keys())
    return [{'period': p, 'count': counts[p]} for p in periods]


def _load_holidays(locale, by, trends):
    """
    Return a dict mapping period string → comma-separated holiday names.
    Requires the `holidays` package (pip install holidays). Silently returns
    {} if the package is not installed or locale is unsupported.
    """
    try:
        import holidays as hol_lib
    except ImportError:
        return {}

    if not trends:
        return {}

    # Derive year range from the trends data
    years = set()
    for row in trends:
        period = row['period']
        try:
            if by == 'week':
                # e.g. '2026-W24' → parse to a date to get the year
                year = int(period.split('-W')[0])
                years.add(year)
            elif by == 'month':
                years.add(int(period.split('-')[0]))
            elif by == 'day':
                years.add(int(period.split('-')[0]))
        except (ValueError, IndexError):
            pass

    if not years:
        return {}

    try:
        country = locale.upper()  # e.g. 'us' → 'US'
        hol_dict = {}
        for year in years:
            hol_dict.update(hol_lib.country_holidays(country, years=year))
    except Exception:
        return {}

    # Map each holiday date to the period format used in trends
    period_map = {}
    for hol_date, hol_name in hol_dict.items():
        try:
            if by == 'week':
                period_key = hol_date.strftime('%G-W%V')
            elif by == 'day':
                period_key = hol_date.strftime('%Y-%m-%d')
            elif by == 'month':
                period_key = hol_date.strftime('%Y-%m')
            else:
                continue
        except Exception:
            continue
        if period_key in period_map:
            period_map[period_key] += f', {hol_name}'
        else:
            period_map[period_key] = hol_name

    return period_map


def render_trends_table(trends, by='week', marathon_threshold=2, locale=None):
    """Print commit cadence table with marathon flags to stdout."""
    holidays_map = _load_holidays(locale, by, trends) if locale else {}

    label = by.capitalize()
    print(f"\n{'PERIOD':<12}  {'COUNT':>5}  {'FLAG':>8}  NOTES")
    print(f"{'-'*12}  {'-'*5}  {'-'*8}  {'-'*40}")

    total = 0
    marathon_count = 0
    for row in trends:
        period = row['period']
        count = row['count']
        is_marathon = count > marathon_threshold
        flag = 'MARATHON' if is_marathon else ''
        notes = holidays_map.get(period, '')
        total += count
        if is_marathon:
            marathon_count += 1
        print(f"{period:<12}  {count:>5}  {flag:>8}  {notes}")

    print(
        f"\nTotal: {total} commits  "
        f"|  {len(trends)} {by}(s) with activity  "
        f"|  Marathons (>{marathon_threshold}/{ by}): {marathon_count}"
    )


def _cmd_discover_commit_trends(args):
    """Handler for: pickaxe discover commit-trends"""
    repo_path = os.path.abspath(getattr(args, 'repo', None) or '.')
    by = getattr(args, 'by', 'week')
    from_date = getattr(args, 'from_date', None)
    to_date = getattr(args, 'to_date', None)
    marathon_threshold = getattr(args, 'marathon_threshold', 2)
    locale = getattr(args, 'holidays', None)

    git_root = find_git_root(repo_path)
    if git_root is None:
        print(f"[pickaxe] error: {repo_path} is not inside a git repo", file=sys.stderr)
        sys.exit(1)

    print(f"[pickaxe discover commit-trends] repo={git_root}  by={by}", file=sys.stderr)

    trends = commit_trends(repo_path, by=by, from_date=from_date, to_date=to_date)

    if not trends:
        print("No commits found for the given range.", file=sys.stderr)
        return

    fmt = getattr(args, 'format', 'table')
    if fmt == 'json':
        print(json.dumps(trends, indent=2))
    else:
        render_trends_table(trends, by=by, marathon_threshold=marathon_threshold, locale=locale)

    if getattr(args, 'save', False):
        summary = {
            'repo': git_root,
            'by': by,
            'from_date': from_date,
            'to_date': to_date,
            'periods': len(trends),
            'total_commits': sum(r['count'] for r in trends),
            'marathons': sum(1 for r in trends if r['count'] > marathon_threshold),
        }
        sessions_dir = os.path.join(git_root, '.pickaxe', 'SESSIONS')
        saved = _save_session_event('discover.commit-trends', git_root, summary, sessions_dir)
        print(f"[pickaxe] session event saved → {saved}", file=sys.stderr)


# --------------------------------------------------------------------------
# BACKUP / RESTORE  (5D safety — portable snapshots)
# --------------------------------------------------------------------------

_BACKUP_SKIP = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', 'dist', 'build',
}


def _copy_working_tree(src, dest):
    """
    Copy working tree from src to dest, preserving symlinks but skipping
    .git directories and common build/cache artifacts.
    Uses dirs_exist_ok=True so it is safe to call on an existing dest (OneDrive
    may hold locks that prevent rmtree on partially-synced trees).
    Falls back to symlinks=False if symlink creation is not permitted (Windows
    without Developer Mode).
    Skips individual files that fail due to MAX_PATH (WinError 3) or file
    locks (WinError 32) — warns to stderr and continues rather than crashing.
    """
    skipped = []

    def _ignore(directory, contents):
        return [c for c in contents if c in _BACKUP_SKIP]

    def _safe_copy(src_path, dst_path, **kwargs):
        try:
            shutil.copy2(src_path, dst_path)
        except OSError as exc:
            skipped.append((src_path, str(exc)))

    os.makedirs(dest, exist_ok=True)
    try:
        shutil.copytree(src, dest, symlinks=True, ignore=_ignore,
                        copy_function=_safe_copy, dirs_exist_ok=True)
    except (OSError, NotImplementedError):
        shutil.copytree(src, dest, symlinks=False, ignore=_ignore,
                        copy_function=_safe_copy, dirs_exist_ok=True)

    if skipped:
        print(f"[pickaxe] working-tree: {len(skipped)} file(s) skipped (locked or path too long):",
              file=sys.stderr)
        for path, reason in skipped[:5]:
            print(f"  SKIP {os.path.basename(path)}: {reason}", file=sys.stderr)
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more", file=sys.stderr)


def backup_workspace(root, dest, skip_working_tree=False, force=False):
    """
    Snapshot all git repos under root to dest.

    Creates:
      <dest>/manifest.json        — repo inventory + metadata
      <dest>/bundles/<name>.bundle — git bundle per discovered repo
      <dest>/working-tree/         — full working-tree copy (no .git dirs)

    Returns the manifest dict.
    Raises FileExistsError if dest already contains a manifest.json or is
    non-empty from a partial run, unless force=True.
    """
    root = os.path.abspath(root)
    dest = os.path.abspath(dest)

    manifest_path = os.path.join(dest, 'manifest.json')
    if not force:
        if os.path.isfile(manifest_path):
            raise FileExistsError(
                f'{manifest_path} already exists — remove it or use --force.'
            )
        # Guard against partial runs: non-empty dir with no manifest
        if os.path.isdir(dest):
            existing = [p for p in os.listdir(dest) if p not in ('bundles',)]
            if existing:
                raise FileExistsError(
                    f'{dest} is non-empty (no manifest.json — partial backup?). '
                    f'Remove it or use --force.'
                )

    bundles_dir = os.path.join(dest, 'bundles')
    os.makedirs(bundles_dir, exist_ok=True)

    entries = discover(root)
    manifest = {
        'pickaxe_version': '0.3.5',
        'created': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
        'root': root,
        'repos': [],
    }

    for entry in entries:
        rel = entry['rel']
        # Build a filesystem-safe bundle name from the relative path
        safe = rel.replace(os.sep, '__').replace('/', '__').lstrip('._') or 'root'
        bundle_rel = os.path.join('bundles', f'{safe}.bundle')
        bundle_abs = os.path.join(dest, bundle_rel)

        r = subprocess.run(
            ['git', '-C', entry['path'], 'bundle', 'create', bundle_abs, '--all'],
            capture_output=True, text=True,
        )
        manifest['repos'].append({
            'rel':       rel,
            'path':      entry['path'],
            'bundle':    bundle_rel,
            'bundle_ok': r.returncode == 0,
            'remote':    entry['remote'],
            'branch':    entry['branch'],
            'flags':     entry['flags'],
        })

    if not skip_working_tree:
        wt_dest = os.path.join(dest, 'working-tree')
        _copy_working_tree(root, wt_dest)
        manifest['working_tree'] = 'working-tree'

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    return manifest


def restore_workspace(backup, dest):
    """
    Restore repos from a pickaxe backup dir.

    For each repo in manifest:
      - git clone <bundle> → <dest>/<rel>
      - re-add origin remote if known

    Returns list of {rel, status} dicts.
    status values: 'ok' | 'already_exists' | 'missing_bundle' | 'clone_failed'
    Raises FileNotFoundError if backup/manifest.json is missing.
    """
    backup = os.path.abspath(backup)
    dest   = os.path.abspath(dest)

    manifest_path = os.path.join(backup, 'manifest.json')
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f'No manifest.json found in: {backup}')

    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)

    results = []
    for repo in manifest.get('repos', []):
        rel    = repo['rel']
        bundle = os.path.join(backup, repo['bundle'])
        target = os.path.join(dest, rel)

        if not os.path.isfile(bundle):
            results.append({'rel': rel, 'status': 'missing_bundle'})
            continue

        if os.path.exists(target):
            results.append({'rel': rel, 'status': 'already_exists'})
            continue

        os.makedirs(os.path.dirname(target) or dest, exist_ok=True)
        r = subprocess.run(
            ['git', 'clone', bundle, target],
            capture_output=True, text=True,
        )
        status = 'ok' if r.returncode == 0 else 'clone_failed'

        if status == 'ok' and repo.get('remote'):
            subprocess.run(
                ['git', '-C', target, 'remote', 'set-url', 'origin', repo['remote']],
                capture_output=True,
            )

        results.append({'rel': rel, 'status': status})

    return results


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


def _render_drift_table(results):
    """Print remote drift summary table to stdout."""
    print(f"\n{'REPO':<22} {'AHEAD':>5} {'BEHIND':>6} {'DIRTY':>5}  {'FLAGS':<16}  REMOTE")
    print(f"{'-'*22} {'-'*5} {'-'*6} {'-'*5}  {'-'*16}  {'-'*40}")
    for r in results:
        flags  = ','.join(r['flags']) if r['flags'] else ''
        remote = r['remote'].replace('https://github.com/', 'gh:') if r['remote'] else '(none)'
        print(f"{r['rel']:<22} {r['ahead']:>5} {r['behind']:>6} {r['dirty']:>5}  {flags:<16}  {remote}")
    needs_action = [r for r in results if r['flags']]
    if needs_action:
        print(f"\n{len(needs_action)} repo(s) need attention: "
              + ', '.join(r['rel'] for r in needs_action))


def render_instruction_bloat_table(findings):
    """Print instruction-bloat findings to stdout."""
    print(f"\n{'KIND':<10}  {'LINES':>11}  {'FILE':<50}  REASON")
    print(f"{'-'*10}  {'-'*11}  {'-'*50}  {'-'*40}")
    for f in findings:
        span = f"{f['start_line']}-{f['end_line']}"
        print(f"{f['kind']:<10}  {span:>11}  {f['file']:<50}  {f['reason']}")
    print(f"\n{len(findings)} finding(s).")


def render_rollup_plan_table(plans):
    """Print a deliver instruction-rollup dry-run plan to stdout."""
    print(f"\n{'STATUS':<17}  {'LINES':>11}  {'SOURCE':<40}  DEST")
    print(f"{'-'*17}  {'-'*11}  {'-'*40}  {'-'*40}")
    for p in plans:
        span = f"{p['start_line']}-{p['end_line']}"
        print(f"{p['status']:<17}  {span:>11}  {p['file']:<40}  {p['dest']}")
    planned = sum(1 for p in plans if p['status'] == 'planned')
    print(f"\n{planned}/{len(plans)} extraction(s) planned. Re-run with --execute to write files.")


def render_rollup_result_table(results):
    """Print deliver instruction-rollup execution results to stdout."""
    print(f"\n{'STATUS':<17}  DEST")
    print(f"{'-'*17}  {'-'*60}")
    for r in results:
        print(f"{r['status']:<17}  {r['dest']}")
    ok = sum(1 for r in results if r['status'] == 'extracted')
    print(f"\n{ok}/{len(results)} extracted.")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _cmd_discover(args):
    noun = getattr(args, 'noun', None)

    # Dispatch on known nouns first
    if noun == 'commit-trends':
        _cmd_discover_commit_trends(args)
        return
    if noun == 'drift':
        root = os.path.abspath(getattr(args, 'root_dir', None) or '.')
        print(f'[pickaxe discover drift] scanning {root} ...', file=sys.stderr)
        results = discover_remote_drift(root)
        if args.format == 'json':
            print(json.dumps(results, indent=2))
        else:
            _render_drift_table(results)
        return

    # Default: repo health map. Treat noun as root_dir if it looks like a path.
    if noun and noun not in DISCOVER_NOUNS:
        root = os.path.abspath(noun)
    else:
        root = os.path.abspath(getattr(args, 'root_dir', None) or '.')

    print(f"[pickaxe discover] scanning {root} ...", file=sys.stderr)
    entries = discover(root)

    # --submodules-only: filter to entries where 'submodule' flag is present
    if getattr(args, 'submodules_only', False):
        entries = [e for e in entries if 'submodule' in e.get('flags', [])]

    if args.format == 'json':
        print(json.dumps(entries, indent=2))
    else:
        render_discover_table(entries)
    if args.save:
        sessions_dir = os.path.join(root, '.pickaxe', 'SESSIONS')
        saved = _save_session_event('discover', root, _build_discover_summary(entries), sessions_dir)
        print(f"[pickaxe] session event saved → {saved}", file=sys.stderr)


def _cmd_diagnose(args):
    noun = getattr(args, 'noun', None)

    if noun == 'instruction-bloat':
        _cmd_diagnose_instruction_bloat(args)
        return

    # Default: single-repo health check. Treat noun as path if it looks like a path.
    if noun and noun not in DIAGNOSE_NOUNS:
        path = os.path.abspath(noun)
    else:
        path = os.path.abspath(getattr(args, 'path', None) or '.')

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


def _cmd_diagnose_instruction_bloat(args):
    """Handler for: pickaxe diagnose instruction-bloat"""
    root = os.path.abspath(getattr(args, 'path', None) or '.')
    max_lines = getattr(args, 'max_lines', 1000)
    max_section_lines = getattr(args, 'max_section_lines', 50)

    print(f'[pickaxe diagnose instruction-bloat] scanning {root} ...', file=sys.stderr)
    findings = diagnose_instruction_bloat(root, max_lines=max_lines, max_section_lines=max_section_lines)

    fmt = getattr(args, 'format', 'table')
    if fmt == 'json':
        print(json.dumps(findings, indent=2))
    else:
        render_instruction_bloat_table(findings)

    if getattr(args, 'save', False):
        summary = {
            'root': root,
            'findings': len(findings),
            'whole_file': sum(1 for f in findings if f['kind'] == 'whole-file'),
            'section': sum(1 for f in findings if f['kind'] == 'section'),
        }
        sessions_dir = os.path.join(root, '.pickaxe', 'SESSIONS')
        saved = _save_session_event('diagnose.instruction-bloat', root, summary, sessions_dir)
        print(f"[pickaxe] session event saved → {saved}", file=sys.stderr)


def _cmd_deliver_instruction_rollup(args):
    """Handler for: pickaxe deliver instruction-rollup"""
    report_path = getattr(args, 'from_report', None)
    if not report_path:
        print('[pickaxe] error: deliver instruction-rollup requires --from-report <findings.json>',
              file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(report_path):
        print(f'[pickaxe] error: report not found: {report_path}', file=sys.stderr)
        sys.exit(1)

    with open(report_path, encoding='utf-8') as f:
        findings = json.load(f)

    root = os.path.abspath(getattr(args, 'root', None) or '.')
    execute = getattr(args, 'execute', False)
    fmt = getattr(args, 'format', 'table')

    if not execute:
        print(f'[pickaxe deliver instruction-rollup] DRY RUN — plan against {root}', file=sys.stderr)
        plans = plan_instruction_rollup(findings, root)
        if fmt == 'json':
            print(json.dumps(plans, indent=2))
        else:
            render_rollup_plan_table(plans)
        return

    print(f'[pickaxe deliver instruction-rollup] EXECUTING against {root}', file=sys.stderr)
    results = execute_instruction_rollup(findings, root)
    if fmt == 'json':
        print(json.dumps(results, indent=2))
    else:
        render_rollup_result_table(results)


def _cmd_deliver(args):
    noun = getattr(args, 'noun', None)
    if noun == 'instruction-rollup':
        _cmd_deliver_instruction_rollup(args)
        return
    print(f'[pickaxe] error: unknown deliver target: {noun}', file=sys.stderr)
    sys.exit(1)


def _render_backup_table(manifest, dest):
    repos = manifest['repos']
    print(f"\n{'STATUS':>8}  {'BUNDLED':>7}  REL")
    print(f"{'-'*8}  {'-'*7}  {'-'*60}")
    for r in repos:
        status = 'ok' if r['bundle_ok'] else 'FAIL'
        bundled = 'yes' if r['bundle_ok'] else 'no'
        print(f"{status:>8}  {bundled:>7}  {r['rel']}")
    ok = sum(1 for r in repos if r['bundle_ok'])
    print(f"\n{ok}/{len(repos)} repo(s) bundled -> {dest}")
    if manifest.get('working_tree'):
        print(f"working-tree  -> {os.path.join(dest, manifest['working_tree'])}")


def _render_restore_table(results):
    print(f"\n{'STATUS':>14}  REL")
    print(f"{'-'*14}  {'-'*60}")
    for r in results:
        print(f"{r['status']:>14}  {r['rel']}")
    ok = sum(1 for r in results if r['status'] == 'ok')
    print(f"\n{ok}/{len(results)} repo(s) restored.")


def _cmd_backup(args):
    root = os.path.abspath(getattr(args, 'root', None) or '.')
    dest = os.path.abspath(args.dest)
    print(f'[pickaxe backup] {root} -> {dest}', file=sys.stderr)
    try:
        manifest = backup_workspace(
            root, dest,
            skip_working_tree=getattr(args, 'skip_working_tree', False),
            force=getattr(args, 'force', False),
        )
    except FileExistsError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
    if args.format == 'json':
        print(json.dumps(manifest, indent=2))
    else:
        _render_backup_table(manifest, dest)


def _cmd_restore(args):
    backup = os.path.abspath(getattr(args, 'backup', None) or '.')
    dest   = os.path.abspath(args.dest)
    print(f'[pickaxe restore] {backup} -> {dest}', file=sys.stderr)
    try:
        results = restore_workspace(backup, dest)
    except FileNotFoundError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        _render_restore_table(results)


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
            'rel':              c['rel'],
            'score':            c['score'],
            'commits':          c['commits'],
            'version':          c['meta'].get('version'),
            'created':          c['meta'].get('created'),
            'author':           c['meta'].get('author'),
            'license':          c['meta'].get('license'),
            'purpose':          c['meta'].get('purpose'),
            'already_extracted': c.get('already_extracted'),
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
        'discover',
        help='Repo map (default) or sub-target: commit-trends | drift',
    )
    p_discover.add_argument(
        'noun', nargs='?', default=None, metavar='target',
        help='Sub-target: commit-trends | drift | (default: repo health map)',
    )
    p_discover.add_argument(
        'root_dir', nargs='?', default='.', metavar='root',
        help='Root dir for repo map (ignored when noun is a known sub-target)',
    )
    p_discover.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_discover.add_argument('--submodules-only', action='store_true', dest='submodules_only',
                             help='Only show repos detected as git submodules (gitlink .git file)')
    p_discover.add_argument('--save', action='store_true',
                             help='Append session event to {root}/.pickaxe/SESSIONS/')
    # commit-trends flags (only used when noun=commit-trends)
    p_discover.add_argument(
        '--repo', default=None, metavar='PATH',
        help='Repo path for commit-trends (default: cwd git root)',
    )
    p_discover.add_argument(
        '--by', choices=['week', 'day', 'month'], default='week',
        help='Cadence granularity (default: week)',
    )
    p_discover.add_argument(
        '--from', dest='from_date', default=None, metavar='DATE',
        help='Start date YYYY-MM-DD (inclusive)',
    )
    p_discover.add_argument(
        '--to', dest='to_date', default=None, metavar='DATE',
        help='End date YYYY-MM-DD (inclusive)',
    )
    p_discover.add_argument(
        '--marathon-threshold', type=int, default=2, metavar='N',
        help='Flag weeks/days/months with > N commits as MARATHON (default: 2)',
    )
    p_discover.add_argument(
        '--holidays', default=None, metavar='LOCALE',
        help='Annotate holiday periods, e.g. "us" (requires: pip install holidays)',
    )
    p_discover.set_defaults(func=_cmd_discover)

    # --- diagnose ---
    p_diagnose = sub.add_parser(
        'diagnose', help='Repo health (default) or sub-target: instruction-bloat'
    )
    p_diagnose.add_argument(
        'noun', nargs='?', default=None, metavar='target',
        help='Sub-target: instruction-bloat | (default: single-repo health check)',
    )
    p_diagnose.add_argument('path', nargs='?', default='.',
                             help='Repo/root path to inspect (ignored when noun is a known sub-target)')
    p_diagnose.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_diagnose.add_argument('--save', action='store_true',
                             help='Append session event to {path}/.pickaxe/SESSIONS/')
    # instruction-bloat flags (only used when noun=instruction-bloat)
    p_diagnose.add_argument('--max-lines', type=int, default=1000, metavar='N',
                             help='Whole-file line-count threshold to flag as bloated (default: 1000)')
    p_diagnose.add_argument('--max-section-lines', type=int, default=50, metavar='N',
                             help='Per-section (##/###) line-count threshold for the scattered-pattern rule (default: 50)')
    p_diagnose.set_defaults(func=_cmd_diagnose)

    # --- deliver ---
    p_deliver = sub.add_parser(
        'deliver',
        help='Execute a treatment plan (dry-run by default): instruction-rollup',
    )
    p_deliver.add_argument(
        'noun', choices=sorted(DELIVER_NOUNS), metavar='target',
        help='Sub-target: instruction-rollup',
    )
    p_deliver.add_argument('root', nargs='?', default='.', metavar='root',
                            help='Workspace root the report paths are relative to (default: cwd)')
    p_deliver.add_argument('--from-report', dest='from_report', default=None, metavar='FILE',
                            help='diagnose instruction-bloat --format json output to act on')
    p_deliver.add_argument('--execute', action='store_true',
                            help='Write files (default: dry-run, prints the plan only)')
    p_deliver.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_deliver.set_defaults(func=_cmd_deliver)

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

    # --- backup ---
    p_backup = sub.add_parser(
        'backup',
        help='Snapshot all repos (bundles + working-tree) to a portable backup dir',
    )
    p_backup.add_argument('root', nargs='?', default='.', help='Workspace root (default: cwd)')
    p_backup.add_argument('--to', required=True, dest='dest', metavar='DEST',
                          help='Backup destination directory')
    p_backup.add_argument('--skip-working-tree', action='store_true', dest='skip_working_tree',
                          help='Bundle repos only — skip working-tree copy')
    p_backup.add_argument('--force', action='store_true',
                          help='Overwrite an existing (partial) backup dest')
    p_backup.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_backup.set_defaults(func=_cmd_backup)

    # --- restore ---
    p_restore = sub.add_parser(
        'restore',
        help='Restore repos from a pickaxe backup (reads manifest.json)',
    )
    p_restore.add_argument('backup', nargs='?', default='.', help='Backup dir containing manifest.json')
    p_restore.add_argument('--to', required=True, dest='dest', metavar='DEST',
                           help='Restore destination directory')
    p_restore.add_argument('--format', '-f', choices=['table', 'json'], default='table')
    p_restore.set_defaults(func=_cmd_restore)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
