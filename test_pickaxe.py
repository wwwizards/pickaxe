#!/usr/bin/env python3
# --------------------------------------------------------------------------
# Script: test_pickaxe.py
# --------------------------------------------------------------------------
# ABSTRACT: Test suite for pickaxe.py.
#     Section 1 — Smoke: v0.1.1 baseline. Must pass before any changes.
#     Section 2 — Diagnose: v0.2 health checks. Failing until implemented.
#     Section 3 — Discover: v0.2 repo map. Failing until implemented.
#
#     Run all:          pytest test_pickaxe.py -v
#     Smoke only:       pytest test_pickaxe.py -v -k Smoke
#     Failing (v0.2):   pytest test_pickaxe.py -v -k "Diagnose or Discover"
#
# CREATED: 26-0526 - BY: wwwizards <github.com/wwwizards>
# VERSION: v0.1.0
# LICENSE: MIT - https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pickaxe  # noqa: E402  (must come after sys.path insert)

HERE = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# FIXTURES
# --------------------------------------------------------------------------

def _make_repo(parent, name, origin_url=None):
    """Create a minimal fake git repo under parent/name. Returns the repo path."""
    repo = parent / name
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    config = "[core]\n\trepositoryformatversion = 0\n"
    if origin_url:
        config += (
            '[remote "origin"]\n'
            f"\turl = {origin_url}\n"
            "\tfetch = +refs/heads/*:refs/remotes/origin/*\n"
        )
    (git_dir / "config").write_text(config)
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    return repo


def _make_submodule_repo(parent, name, origin_url=None):
    """
    Create a minimal fake submodule worktree under parent/name.
    The .git entry is a gitlink file (not a directory), mirroring what
    `git submodule add` produces.  The real git store lives at
    parent/.git/modules/<name> so that _resolve_git_dir can traverse it.
    """
    # Real git store (simulates .git/modules/<name> inside the parent repo)
    git_modules_dir = parent / ".git" / "modules" / name
    git_modules_dir.mkdir(parents=True)
    config = "[core]\n\trepositoryformatversion = 0\n"
    if origin_url:
        config += (
            '[remote "origin"]\n'
            f"\turl = {origin_url}\n"
            "\tfetch = +refs/heads/*:refs/remotes/origin/*\n"
        )
    (git_modules_dir / "config").write_text(config)
    (git_modules_dir / "HEAD").write_text("ref: refs/heads/main\n")

    # Submodule worktree — .git is a gitlink file
    workdir = parent / name
    workdir.mkdir()
    rel_gitdir = os.path.relpath(str(git_modules_dir), str(workdir))
    (workdir / ".git").write_text(f"gitdir: {rel_gitdir}\n")
    return workdir


@pytest.fixture
def repo_with_origin(tmp_path):
    return _make_repo(
        tmp_path, "my-repo", "https://github.com/wwwizards/test-repo.git"
    )


@pytest.fixture
def repo_no_origin(tmp_path):
    return _make_repo(tmp_path, "no-origin-repo")


@pytest.fixture
def repo_stripped_config(tmp_path):
    """git repo where .git/config is absent (stripped)."""
    repo = tmp_path / "stripped-repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    # intentionally no config file
    return repo


@pytest.fixture
def detached_folder(tmp_path):
    """Plain folder, no .git anywhere."""
    folder = tmp_path / "detached"
    folder.mkdir()
    (folder / "script.py").write_text("print('hello')\n")
    return folder


@pytest.fixture
def script_full_header(tmp_path):
    f = tmp_path / "my_tool.py"
    f.write_text(
        "#!/usr/bin/env python3\n"
        "# VERSION: 1.2.3\n"
        "# CREATED: 2026-01-01\n"
        "# ABSTRACT: Does something useful for testing.\n"
        "# LICENSE: MIT\n"
        "print('hello')\n"
    )
    return f


@pytest.fixture
def script_minimal(tmp_path):
    f = tmp_path / "bare.py"
    f.write_text("print('bare')\n")
    return f


# --------------------------------------------------------------------------
# SMOKE — v0.1.1 baseline
# --------------------------------------------------------------------------

class TestSmoke:

    def test_module_imports(self):
        for fn in ("find_git_root", "parse_header", "score_candidate",
                   "extraction_script", "scan"):
            assert hasattr(pickaxe, fn), f"missing: pickaxe.{fn}"

    def test_find_git_root_finds_own_repo(self):
        root = pickaxe.find_git_root(HERE)
        assert root is not None
        assert os.path.isdir(os.path.join(root, ".git"))

    def test_find_git_root_returns_none_for_bare_tmp(self, tmp_path):
        assert pickaxe.find_git_root(str(tmp_path)) is None

    def test_parse_header_full(self, script_full_header):
        meta = pickaxe.parse_header(str(script_full_header))
        assert meta["shebang"] is True
        assert meta["version"] == "1.2.3"
        assert meta["created"] == "2026-01-01"
        assert meta["purpose"] is not None
        assert meta["license"] == "MIT"

    def test_parse_header_minimal(self, script_minimal):
        meta = pickaxe.parse_header(str(script_minimal))
        assert meta["version"] is None
        assert meta["shebang"] is False

    def test_parse_header_on_pickaxe_itself(self):
        meta = pickaxe.parse_header(os.path.join(HERE, "pickaxe.py"))
        assert meta["version"] is not None
        assert meta["version"].startswith("0.")

    def test_score_full_header(self, script_full_header):
        meta = pickaxe.parse_header(str(script_full_header))
        # shebang(1) + version(2) + created(1) + purpose(1) + license(1) + low-commits(1) = 7
        score = pickaxe.score_candidate(meta, git_commits=1)
        assert score >= 6

    def test_score_minimal(self, script_minimal):
        meta = pickaxe.parse_header(str(script_minimal))
        assert pickaxe.score_candidate(meta, git_commits=0) == 0

    def test_extraction_script_is_runnable_bash(self):
        git_root = pickaxe.find_git_root(HERE)
        result = pickaxe.extraction_script(git_root, os.path.join(HERE, "pickaxe.py"))
        assert "filter-repo" in result
        assert "git clone" in result

    def test_cli_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    # --- PX-B3: already_extracted annotation ---

    def test_scan_candidate_has_already_extracted_key(self, tmp_path):
        """Every scan candidate dict must include 'already_extracted' key."""
        # Script inside a fresh isolated repo — not already extracted
        repo = tmp_path / "myrepo"
        repo.mkdir()
        subprocess.run(['git', 'init', str(repo)], capture_output=True)
        script = repo / "tool.py"
        script.write_text("#!/usr/bin/env python3\n# VERSION: 1.0.0\n# PURPOSE: test\n# LICENSE: MIT\n# CREATED: 2026-01-01\npass\n")
        subprocess.run(['git', '-C', str(repo), 'add', '.'], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-m', 'init',
                        '-c', 'user.email=t@t.com', '-c', 'user.name=T',
                        '-c', 'commit.gpgsign=false'], capture_output=True)
        candidates = pickaxe.scan(str(tmp_path), ['.py'], min_score=0)
        assert len(candidates) >= 1
        for c in candidates:
            assert 'already_extracted' in c

    def test_scan_same_repo_not_annotated_as_extracted(self, tmp_path):
        """A file inside the scan root's own repo must have already_extracted=None."""
        repo = tmp_path / "myrepo"
        repo.mkdir()
        subprocess.run(['git', 'init', str(repo)], capture_output=True)
        script = repo / "tool.py"
        script.write_text("#!/usr/bin/env python3\n# VERSION: 1.0.0\n# PURPOSE: test\n# LICENSE: MIT\n# CREATED: 2026-01-01\npass\n")
        subprocess.run(['git', '-C', str(repo), 'add', '.'], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-m', 'init',
                        '-c', 'user.email=t@t.com', '-c', 'user.name=T',
                        '-c', 'commit.gpgsign=false'], capture_output=True)
        # Scan from within the repo — same git root, not extracted
        candidates = pickaxe.scan(str(repo), ['.py'], min_score=0)
        for c in candidates:
            assert c['already_extracted'] is None


# --------------------------------------------------------------------------
# DIAGNOSE — repo health inspection  (v0.2 — failing until implemented)
# --------------------------------------------------------------------------

class TestDiagnose:

    def test_diagnose_function_exists(self):
        assert hasattr(pickaxe, "diagnose"), "pickaxe.diagnose() not implemented"

    def test_healthy_repo_flags_ok(self, repo_with_origin):
        r = pickaxe.diagnose(str(repo_with_origin))
        assert r["has_git"] is True
        assert r["has_origin"] is True
        assert "ok" in r["flags"]
        assert "missing_git" not in r["flags"]
        assert "missing_origin" not in r["flags"]

    def test_detached_folder_flags_missing_git(self, detached_folder):
        r = pickaxe.diagnose(str(detached_folder))
        assert r["has_git"] is False
        assert "missing_git" in r["flags"]

    def test_repo_without_origin_flags_missing_origin(self, repo_no_origin):
        r = pickaxe.diagnose(str(repo_no_origin))
        assert r["has_git"] is True
        assert r["has_origin"] is False
        assert "missing_origin" in r["flags"]

    def test_repo_stripped_config_flagged(self, repo_stripped_config):
        r = pickaxe.diagnose(str(repo_stripped_config))
        assert r["has_git"] is True
        assert "stripped_config" in r["flags"] or "missing_origin" in r["flags"]

    def test_diagnose_returns_remote_url(self, repo_with_origin):
        r = pickaxe.diagnose(str(repo_with_origin))
        assert r["remote_url"] == "https://github.com/wwwizards/test-repo.git"

    def test_diagnose_no_origin_remote_url_is_none(self, repo_no_origin):
        r = pickaxe.diagnose(str(repo_no_origin))
        assert r["remote_url"] is None

    def test_diagnose_on_pickaxe_itself(self):
        r = pickaxe.diagnose(HERE)
        assert r["has_git"] is True
        assert r["has_origin"] is True

    def test_diagnose_never_mutates(self, repo_no_origin):
        """Running diagnose must not create or modify any files."""
        before = set(os.listdir(str(repo_no_origin)))
        pickaxe.diagnose(str(repo_no_origin))
        after = set(os.listdir(str(repo_no_origin)))
        assert before == after

    # --- gitlink / submodule ---

    def test_diagnose_gitlink_has_git_true(self, tmp_path):
        """A submodule worktree (.git as gitlink file) must report has_git=True."""
        sub = _make_submodule_repo(tmp_path, "my-sub", "https://github.com/test/my-sub.git")
        r = pickaxe.diagnose(str(sub))
        assert r["has_git"] is True
        assert "missing_git" not in r["flags"]

    def test_diagnose_gitlink_flags_submodule(self, tmp_path):
        """A gitlink repo must carry the 'submodule' flag."""
        sub = _make_submodule_repo(tmp_path, "my-sub", "https://github.com/test/my-sub.git")
        r = pickaxe.diagnose(str(sub))
        assert "submodule" in r["flags"]

    def test_diagnose_gitlink_resolves_origin(self, tmp_path):
        """diagnose() must read origin URL from the resolved gitdir, not the gitlink file."""
        sub = _make_submodule_repo(tmp_path, "my-sub", "https://github.com/test/my-sub.git")
        r = pickaxe.diagnose(str(sub))
        assert r["has_origin"] is True
        assert r["remote_url"] == "https://github.com/test/my-sub.git"

    def test_diagnose_gitlink_no_origin(self, tmp_path):
        """Gitlink repo without an origin remote must flag missing_origin."""
        sub = _make_submodule_repo(tmp_path, "my-sub")  # no origin_url
        r = pickaxe.diagnose(str(sub))
        assert r["has_git"] is True
        assert "missing_origin" in r["flags"]


# --------------------------------------------------------------------------
# DISCOVER — local repo map  (v0.2 — failing until implemented)
# --------------------------------------------------------------------------

class TestDiscover:

    def test_discover_function_exists(self):
        assert hasattr(pickaxe, "discover"), "pickaxe.discover() not implemented"

    def test_discover_empty_dir_returns_empty(self, tmp_path):
        assert pickaxe.discover(str(tmp_path)) == []

    def test_discover_finds_single_repo(self, tmp_path):
        repo = _make_repo(tmp_path, "alpha", "https://github.com/test/alpha.git")
        results = pickaxe.discover(str(tmp_path))
        paths = [r["path"] for r in results]
        assert str(repo) in paths

    def test_discover_entry_has_required_keys(self, tmp_path):
        _make_repo(tmp_path, "beta", "https://github.com/test/beta.git")
        results = pickaxe.discover(str(tmp_path))
        assert len(results) == 1
        entry = results[0]
        for key in ("path", "rel", "remote", "branch", "flags", "health_ok"):
            assert key in entry, f"missing key: {key}"

    def test_discover_healthy_repo_is_health_ok(self, tmp_path):
        _make_repo(tmp_path, "gamma", "https://github.com/test/gamma.git")
        results = pickaxe.discover(str(tmp_path))
        entry = results[0]
        assert entry["health_ok"] is True

    def test_discover_unhealthy_repo_is_not_health_ok(self, tmp_path):
        _make_repo(tmp_path, "delta")  # no origin
        results = pickaxe.discover(str(tmp_path))
        entry = results[0]
        assert entry["health_ok"] is False

    def test_discover_finds_multiple_repos(self, tmp_path):
        for name in ("repo-a", "repo-b", "repo-c"):
            _make_repo(tmp_path, name, f"https://github.com/test/{name}.git")
        results = pickaxe.discover(str(tmp_path))
        assert len(results) == 3

    def test_discover_returns_remote_url(self, tmp_path):
        _make_repo(tmp_path, "epsilon", "https://github.com/test/epsilon.git")
        results = pickaxe.discover(str(tmp_path))
        assert results[0]["remote"] == "https://github.com/test/epsilon.git"

    def test_discover_returns_branch(self, tmp_path):
        _make_repo(tmp_path, "zeta", "https://github.com/test/zeta.git")
        results = pickaxe.discover(str(tmp_path))
        assert results[0]["branch"] == "main"

    def test_discover_never_mutates(self, tmp_path):
        _make_repo(tmp_path, "eta", "https://github.com/test/eta.git")
        before = set(p.name for p in tmp_path.iterdir())
        pickaxe.discover(str(tmp_path))
        after = set(p.name for p in tmp_path.iterdir())
        assert before == after

    def test_discover_on_pickaxe_root_finds_itself(self):
        """Scanning pickaxe's own parent should include pickaxe in results."""
        parent = os.path.dirname(HERE)
        results = pickaxe.discover(parent)
        paths = [r["path"] for r in results]
        assert HERE in paths

    # --- gitlink / submodule ---

    def test_discover_finds_gitlink_submodule(self, tmp_path):
        """discover() must find repos where .git is a gitlink file (submodules)."""
        _make_submodule_repo(tmp_path, "my-sub", "https://github.com/test/my-sub.git")
        results = pickaxe.discover(str(tmp_path))
        rels = [r["rel"] for r in results]
        assert "my-sub" in rels

    def test_discover_gitlink_entry_flagged_submodule(self, tmp_path):
        """Gitlink repos surfaced by discover() must carry the 'submodule' flag."""
        _make_submodule_repo(tmp_path, "my-sub", "https://github.com/test/my-sub.git")
        results = pickaxe.discover(str(tmp_path))
        sub_entry = next(r for r in results if r["rel"] == "my-sub")
        assert "submodule" in sub_entry["flags"]

    def test_discover_gitlink_health_ok_with_origin(self, tmp_path):
        """A gitlink repo with a valid origin must be reported as health_ok."""
        _make_submodule_repo(tmp_path, "my-sub", "https://github.com/test/my-sub.git")
        results = pickaxe.discover(str(tmp_path))
        sub_entry = next(r for r in results if r["rel"] == "my-sub")
        assert sub_entry["health_ok"] is True

    # --- PX-B1: --submodules-only ---

    def test_cli_discover_submodules_only_returns_only_submodules(self, tmp_path):
        """--submodules-only must exclude normal repos, keep only gitlink entries."""
        _make_repo(tmp_path, "normal-repo", "https://github.com/test/normal.git")
        _make_submodule_repo(tmp_path, "sub-repo", "https://github.com/test/sub.git")
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "discover", str(tmp_path), "--submodules-only", "--format", "json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        rels = [e["rel"] for e in data]
        assert "sub-repo" in rels
        assert "normal-repo" not in rels

    def test_cli_discover_submodules_only_empty_when_no_submodules(self, tmp_path):
        """--submodules-only on a tree with no gitlinks must return empty list."""
        _make_repo(tmp_path, "plain", "https://github.com/test/plain.git")
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "discover", str(tmp_path), "--submodules-only", "--format", "json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data == []


# --------------------------------------------------------------------------
# SESSION LOGGING — v0.3.0  (--save flag)
# --------------------------------------------------------------------------

class TestSessionLogging:

    def test_save_session_event_creates_file(self, tmp_path):
        sessions_dir = str(tmp_path / ".pickaxe" / "SESSIONS")
        saved = pickaxe._save_session_event(
            "discover", str(tmp_path), {"repos_found": 1, "health_ok": 1, "flag_counts": {}}, sessions_dir
        )
        assert os.path.isfile(saved)

    def test_save_session_event_is_valid_ndjson(self, tmp_path):
        sessions_dir = str(tmp_path / ".pickaxe" / "SESSIONS")
        pickaxe._save_session_event("discover", str(tmp_path), {"repos_found": 2}, sessions_dir)
        files = list(os.scandir(sessions_dir))
        assert len(files) == 1
        lines = open(files[0].path, encoding="utf-8").read().strip().splitlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["phase"] == "discover"
        assert "ts" in event
        assert "target" in event
        assert "result" in event

    def test_save_session_event_target_is_relative(self, tmp_path):
        sessions_dir = str(tmp_path / ".pickaxe" / "SESSIONS")
        pickaxe._save_session_event("discover", str(tmp_path), {}, sessions_dir)
        filepath = list(os.scandir(sessions_dir))[0].path
        event = json.loads(open(filepath, encoding="utf-8").readline())
        # target must not be absolute (no drive letter or leading slash)
        assert not os.path.isabs(event["target"])

    def test_save_session_event_uses_forward_slashes(self, tmp_path):
        sessions_dir = str(tmp_path / ".pickaxe" / "SESSIONS")
        pickaxe._save_session_event("diagnose", str(tmp_path / "some" / "repo"), {}, sessions_dir)
        filepath = list(os.scandir(sessions_dir))[0].path
        event = json.loads(open(filepath, encoding="utf-8").readline())
        assert "\\" not in event["target"]

    def test_save_appends_multiple_events(self, tmp_path):
        sessions_dir = str(tmp_path / ".pickaxe" / "SESSIONS")
        for i in range(3):
            pickaxe._save_session_event("discover", str(tmp_path), {"run": i}, sessions_dir)
        filepath = list(os.scandir(sessions_dir))[0].path
        lines = open(filepath, encoding="utf-8").read().strip().splitlines()
        assert len(lines) == 3
        for line in lines:
            json.loads(line)  # each line must be valid JSON

    def test_build_discover_summary_counts_flags(self, tmp_path):
        entries = [
            {"health_ok": True,  "flags": ["ok"]},
            {"health_ok": False, "flags": ["missing_origin"]},
            {"health_ok": False, "flags": ["missing_origin", "stripped_config"]},
        ]
        s = pickaxe._build_discover_summary(entries)
        assert s["repos_found"] == 3
        assert s["health_ok"] == 1
        assert s["flag_counts"]["missing_origin"] == 2
        assert s["flag_counts"]["stripped_config"] == 1

    def test_build_diagnose_summary_keys(self, repo_with_origin):
        result = pickaxe.diagnose(str(repo_with_origin))
        s = pickaxe._build_diagnose_summary(result)
        assert "has_git" in s
        assert "has_origin" in s
        assert "flags" in s

    def test_cli_discover_save_creates_sessions_dir(self, tmp_path):
        """CLI --save flag must create .pickaxe/SESSIONS/ and write an event."""
        # Create a minimal git repo inside tmp_path so discover finds something
        repo = tmp_path / "myrepo"
        repo.mkdir()
        git_dir = repo / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text(
            "[core]\n\trepositoryformatversion = 0\n"
            "[remote \"origin\"]\n\turl = https://github.com/test/test.git\n"
        )
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "discover", str(tmp_path), "--save"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        sessions_dir = tmp_path / ".pickaxe" / "SESSIONS"
        assert sessions_dir.is_dir(), "Sessions dir not created"
        files = list(sessions_dir.iterdir())
        assert len(files) == 1
        event = json.loads(open(files[0], encoding="utf-8").readline())
        assert event["phase"] == "discover"

    def test_build_scan_summary_keys(self, tmp_path):
        """_build_scan_summary must return required trajectory keys."""
        # Create minimal candidate list with two different scores
        candidates = [
            {"score": 5, "rel": "a.py"},
            {"score": 5, "rel": "b.py"},
            {"score": 3, "rel": "c.ps1"},
        ]
        s = pickaxe._build_scan_summary(candidates, str(tmp_path))
        assert s["candidates_found"] == 3
        assert s["top_score"] == 5
        assert "score_distribution" in s
        assert s["score_distribution"][5] == 2
        assert s["score_distribution"][3] == 1

    def test_build_scan_summary_empty(self, tmp_path):
        """_build_scan_summary on empty candidate list must not raise."""
        s = pickaxe._build_scan_summary([], str(tmp_path))
        assert s["candidates_found"] == 0
        assert s["top_score"] == 0

    def test_cli_scan_save_creates_sessions_entry(self, tmp_path):
        """CLI `scan --save` must create a session event file under .pickaxe/SESSIONS/."""
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "scan", str(tmp_path), "--save"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"scan --save failed: {result.stderr}"
        sessions_dir = tmp_path / ".pickaxe" / "SESSIONS"
        assert sessions_dir.is_dir(), "Sessions dir not created by scan --save"
        files = list(sessions_dir.iterdir())
        assert len(files) == 1
        event = json.loads(open(files[0], encoding="utf-8").readline())
        assert event["phase"] == "scan"
        assert event["result"]["candidates_found"] == 0  # empty dir → 0 candidates


# --------------------------------------------------------------------------
# COMMIT TRENDS — discover commit-trends  (v0.3.3)
# --------------------------------------------------------------------------

def _make_git_repo_with_commits(tmp_path, name, commit_dates):
    """
    Create a real git repo at tmp_path/name with one empty commit per date.
    commit_dates: list of ISO date strings ('YYYY-MM-DD').
    Returns the repo path as a str.

    Writes .git/config directly to avoid inheriting global git settings
    (gpgsign, safe.directory, etc.) that would cause commits to fail in
    tmp dirs on machines with strict git configs.
    """
    repo = tmp_path / name
    repo.mkdir()

    # Init repo
    subprocess.check_call(["git", "init", "-b", "main", str(repo)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Write config directly — bypasses global gpgsign, safe.directory, etc.
    git_config = (
        "[core]\n"
        "\trepositoryformatversion = 0\n"
        "\tfilemode = false\n"
        "\tbare = false\n"
        "[user]\n"
        "\temail = t@t.com\n"
        "\tname = Test\n"
        "[commit]\n"
        "\tgpgsign = false\n"
    )
    (repo / ".git" / "config").write_text(git_config, encoding="utf-8")

    # Use ISO 8601 datetime format (git accepts bare YYYY-MM-DD but some builds don't)
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "t@t.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "t@t.com",
        "GIT_CONFIG_NOSYSTEM": "1",    # skip /etc/gitconfig
        "HOME": str(tmp_path),         # skip ~/.gitconfig on this machine
    }

    for i, date in enumerate(commit_dates):
        iso_date = f"{date}T12:00:00 +0000"
        date_env = {**env, "GIT_AUTHOR_DATE": iso_date, "GIT_COMMITTER_DATE": iso_date}
        (repo / f"file{i}.txt").write_text(f"commit {i}\n")
        subprocess.check_call(["git", "-C", str(repo), "add", "."],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(
            ["git", "-C", str(repo),
             "-c", "commit.gpgsign=false",
             "commit", "--allow-empty", "-m", f"commit {i}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=date_env,
        )
    return str(repo)


class TestCommitTrends:

    def test_commit_trends_function_exists(self):
        assert hasattr(pickaxe, "commit_trends"), "pickaxe.commit_trends() not implemented"

    def test_commit_trends_returns_list(self, tmp_path):
        repo = _make_git_repo_with_commits(tmp_path, "r1", ["2026-01-05", "2026-01-06"])
        result = pickaxe.commit_trends(repo, by="week")
        assert isinstance(result, list)

    def test_commit_trends_entries_have_required_keys(self, tmp_path):
        repo = _make_git_repo_with_commits(tmp_path, "r2", ["2026-01-05"])
        result = pickaxe.commit_trends(repo, by="week")
        assert len(result) >= 1
        for entry in result:
            assert "period" in entry
            assert "count" in entry

    def test_commit_trends_week_format(self, tmp_path):
        """Periods must be ISO week strings like '2026-W02'."""
        repo = _make_git_repo_with_commits(tmp_path, "r3", ["2026-01-05", "2026-01-06"])
        result = pickaxe.commit_trends(repo, by="week")
        import re
        for entry in result:
            assert re.match(r"\d{4}-W\d{2}$", entry["period"]), \
                f"unexpected period format: {entry['period']}"

    def test_commit_trends_day_format(self, tmp_path):
        """by='day' must produce YYYY-MM-DD periods."""
        repo = _make_git_repo_with_commits(tmp_path, "r4", ["2026-01-05", "2026-01-06"])
        result = pickaxe.commit_trends(repo, by="day")
        import re
        for entry in result:
            assert re.match(r"\d{4}-\d{2}-\d{2}$", entry["period"]), \
                f"unexpected day format: {entry['period']}"

    def test_commit_trends_month_format(self, tmp_path):
        """by='month' must produce YYYY-MM periods."""
        repo = _make_git_repo_with_commits(tmp_path, "r5", ["2026-01-05", "2026-02-10"])
        result = pickaxe.commit_trends(repo, by="month")
        import re
        for entry in result:
            assert re.match(r"\d{4}-\d{2}$", entry["period"]), \
                f"unexpected month format: {entry['period']}"

    def test_commit_trends_counts_correctly(self, tmp_path):
        """3 commits in the same week → count=3 for that week."""
        repo = _make_git_repo_with_commits(
            tmp_path, "r6",
            ["2026-01-05", "2026-01-06", "2026-01-07"],  # all in 2026-W02
        )
        result = pickaxe.commit_trends(repo, by="week")
        week = next((r for r in result if r["period"] == "2026-W02"), None)
        assert week is not None, f"2026-W02 not found in {result}"
        assert week["count"] == 3

    def test_commit_trends_empty_repo_returns_empty(self, tmp_path):
        """A repo with no commits must return []."""
        repo = tmp_path / "empty-repo"
        repo.mkdir()
        subprocess.check_call(["git", "init", str(repo)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = pickaxe.commit_trends(str(repo), by="week")
        assert result == []

    def test_commit_trends_non_repo_returns_empty(self, tmp_path):
        """A plain directory (no .git) must return []."""
        plain = tmp_path / "plain"
        plain.mkdir()
        result = pickaxe.commit_trends(str(plain), by="week")
        assert result == []

    def test_commit_trends_sorted_chronologically(self, tmp_path):
        """Periods must be in ascending order."""
        repo = _make_git_repo_with_commits(
            tmp_path, "r7",
            ["2026-01-05", "2026-03-02", "2026-02-09"],  # out of order input
        )
        result = pickaxe.commit_trends(repo, by="week")
        periods = [r["period"] for r in result]
        assert periods == sorted(periods)

    def test_commit_trends_from_date_filter(self, tmp_path):
        """--from should exclude commits before the given date."""
        repo = _make_git_repo_with_commits(
            tmp_path, "r8",
            ["2026-01-05", "2026-03-02"],
        )
        result = pickaxe.commit_trends(repo, by="month", from_date="2026-02-01")
        # Only the March commit should appear
        months = [r["period"] for r in result]
        assert "2026-01" not in months
        assert "2026-03" in months

    def test_commit_trends_to_date_filter(self, tmp_path):
        """--to should exclude commits after the given date."""
        repo = _make_git_repo_with_commits(
            tmp_path, "r9",
            ["2026-01-05", "2026-03-02"],
        )
        result = pickaxe.commit_trends(repo, by="month", to_date="2026-02-01")
        months = [r["period"] for r in result]
        assert "2026-03" not in months
        assert "2026-01" in months

    def test_commit_trends_on_live_pickaxe_repo(self):
        """Smoke: running against pickaxe's own repo must return non-empty list."""
        result = pickaxe.commit_trends(HERE, by="week")
        assert len(result) > 0, "Expected at least one week of commits in pickaxe repo"
        assert all("count" in r and r["count"] > 0 for r in result)

    def test_render_trends_table_function_exists(self):
        assert hasattr(pickaxe, "render_trends_table")

    def test_render_trends_table_outputs_header(self, tmp_path, capsys):
        """render_trends_table must print PERIOD and COUNT headers."""
        trends = [{"period": "2026-W01", "count": 3}, {"period": "2026-W02", "count": 1}]
        pickaxe.render_trends_table(trends, by="week", marathon_threshold=2)
        out = capsys.readouterr().out
        assert "PERIOD" in out
        assert "COUNT" in out

    def test_render_trends_table_flags_marathon(self, tmp_path, capsys):
        """A period with count > threshold must show MARATHON in output."""
        trends = [{"period": "2026-W24", "count": 5}]
        pickaxe.render_trends_table(trends, by="week", marathon_threshold=2)
        out = capsys.readouterr().out
        assert "MARATHON" in out

    def test_render_trends_table_no_false_marathon(self, tmp_path, capsys):
        """A period at exactly the threshold must NOT be flagged as marathon."""
        trends = [{"period": "2026-W24", "count": 2}]
        pickaxe.render_trends_table(trends, by="week", marathon_threshold=2)
        out = capsys.readouterr().out
        assert "MARATHON" not in out

    def test_cli_discover_commit_trends_exits_zero(self, tmp_path):
        """CLI: pickaxe discover commit-trends --repo <live-repo> must exit 0."""
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "discover", "commit-trends", "--repo", HERE],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"non-zero exit: {result.stderr}"

    def test_cli_discover_commit_trends_json(self, tmp_path):
        """CLI: --format json must emit valid JSON list."""
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "discover", "commit-trends", "--repo", HERE, "--format", "json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"non-zero exit: {result.stderr}"
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "period" in data[0]
        assert "count" in data[0]

    def test_cli_discover_commit_trends_by_month(self, tmp_path):
        """CLI: --by month must produce month-format periods in JSON output."""
        import re
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "discover", "commit-trends", "--repo", HERE,
             "--format", "json", "--by", "month"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"non-zero exit: {result.stderr}"
        data = json.loads(result.stdout)
        for entry in data:
            assert re.match(r"\d{4}-\d{2}$", entry["period"]), \
                f"unexpected month format: {entry['period']}"

    def test_cli_discover_default_still_works(self, tmp_path):
        """Backward compat: pickaxe discover <path> (no noun) must still work."""
        _make_repo(tmp_path, "compat-repo", "https://github.com/test/compat.git")
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "pickaxe.py"),
             "discover", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"non-zero exit: {result.stderr}"
        assert "compat-repo" in result.stdout

