#!/usr/bin/env python3
"""
run_tests.py
============
Standalone test runner — no pytest required.
Runs the same tests as test_all.py with coloured output.

Usage:
    python run_tests.py              # run all tests
    python run_tests.py auth         # run tests matching "auth"
    python run_tests.py cli verify   # run tests matching cli OR verify
"""
from __future__ import annotations

import inspect
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── Colours ──────────────────────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def _c(text, *codes): return "".join(codes) + str(text) + RESET

# ── Simple fixture system ─────────────────────────────────────────────
import tempfile, os

class _TmpPath:
    """Mimics pytest's tmp_path fixture."""
    def __init__(self):
        self._dir = tempfile.mkdtemp()
    @property
    def path(self): return Path(self._dir)
    def cleanup(self): import shutil; shutil.rmtree(self._dir, ignore_errors=True)

class _MonkeyPatch:
    """Mimics pytest's monkeypatch fixture."""
    def __init__(self):
        self._restore = []
    def setenv(self, key, value):
        old = os.environ.get(key)
        os.environ[key] = value
        self._restore.append(('env', key, old))
    def undo(self):
        for kind, key, old in reversed(self._restore):
            if kind == 'env':
                if old is None: os.environ.pop(key, None)
                else: os.environ[key] = old

# ── Test discovery and runner ─────────────────────────────────────────

def _make_fixtures(method):
    """Return kwargs dict based on parameter names of the method."""
    sig    = inspect.signature(method)
    kwargs = {}
    tmp_paths = []
    monkeys   = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if name == "tmp_path":
            tp = _TmpPath()
            tmp_paths.append(tp)
            kwargs[name] = tp.path
        elif name == "monkeypatch":
            mp = _MonkeyPatch()
            monkeys.append(mp)
            kwargs[name] = mp
        elif name == "db":
            from pybackup.db.database import Database
            kwargs[name] = Database(":memory:")
        elif name == "router_and_db":
            import tempfile, os
            from pybackup.db.database import Database
            from pybackup.server.httpserver import Router, PyBackupHandler
            from pybackup.server.handlers import register_routes
            from pybackup.auth import UserDB, sessions
            _td = tempfile.mkdtemp()
            _dbp = os.path.join(_td, "test.db")
            db = Database(_dbp)
            udb = UserDB(_dbp)
            _uid = udb.create_user("testadmin", "Admin1234!", role="admin")
            _tok = sessions.create(_uid, "testadmin", "admin")
            router = Router()
            register_routes(router)
            PyBackupHandler.user_db = udb
            kwargs[name] = (router, db, _tok)
        elif name == "router":
            from pybackup.server.httpserver import Router
            from pybackup.server.handlers import register_routes
            r = Router(); register_routes(r)
            kwargs[name] = r
        elif name == "api_req":
            from pybackup.server.httpserver import Request
            from urllib.parse import parse_qs
            def _make(method, path, query="", body=b""):
                r = Request(method, path, parse_qs(query), {}, body)
                return r
            kwargs[name] = _make
    return kwargs, tmp_paths, monkeys

def _cleanup(tmp_paths, monkeys):
    for mp in monkeys: mp.undo()
    for tp in tmp_paths: tp.cleanup()

def run_all(filters: list[str] | None = None):
    # Import all test classes from test_all
    import tests.test_all as T

    classes = [
        T.TestExceptions, T.TestSecurity, T.TestConfig,
        T.TestVerifier, T.TestManifest, T.TestFilesEngine,
        T.TestMongoEngine, T.TestPostgresEngine, T.TestMySQLEngine,
        T.TestMSSQLEngine, T.TestDatabase, T.TestRouter,
        T.TestAPIHandlers, T.TestCLI,
    ]

    total = passed = failed = skipped = 0
    failures: list[tuple[str,str]] = []
    start_all = time.time()

    for cls in classes:
        methods = [
            (name, getattr(cls, name))
            for name in dir(cls)
            if name.startswith("test_") and callable(getattr(cls, name))
        ]
        if not methods:
            continue

        # Filter
        if filters:
            methods = [
                (n, m) for n, m in methods
                if any(f.lower() in (cls.__name__ + "::" + n).lower() for f in filters)
            ]
        if not methods:
            continue

        print(f"\n{_c(cls.__name__, BOLD, CYAN)}")
        print(_c("  " + "─" * 50, DIM))

        instance = cls()
        for name, method in sorted(methods, key=lambda x: x[0]):
            total += 1
            label = f"  {name}"
            kwargs, tmp_paths, monkeys = _make_fixtures(method)
            t0 = time.time()
            try:
                method(instance, **kwargs)
                ms = (time.time() - t0) * 1000
                passed += 1
                print(f"  {_c('PASS', GREEN)}  {name}  {_c(f'{ms:.0f}ms', DIM)}")
            except Exception as exc:
                ms = (time.time() - t0) * 1000
                failed += 1
                tb = traceback.format_exc().strip().split("\n")[-1]
                print(f"  {_c('FAIL', RED)}  {name}  {_c(f'{ms:.0f}ms', DIM)}")
                print(f"       {_c(tb, RED, DIM)}")
                failures.append((f"{cls.__name__}::{name}", tb))
            finally:
                _cleanup(tmp_paths, monkeys)

    # ── Summary ──────────────────────────────────────────────────────
    elapsed = time.time() - start_all
    print()
    print(_c("=" * 60, DIM))
    print(
        f"  {_c(f'{passed} passed', GREEN, BOLD)}"
        f"  {_c(f'{failed} failed', RED, BOLD) if failed else ''}"
        f"  {_c(f'in {elapsed:.2f}s', DIM)}"
    )
    if failures:
        print()
        print(_c("  Failures:", RED, BOLD))
        for name, msg in failures:
            print(f"    {_c('✘', RED)} {name}")
            print(f"      {_c(msg, DIM)}")
    else:
        print(f"  {_c('All tests passed ✔', GREEN, BOLD)}")
    print(_c("=" * 60, DIM))
    return failed

if __name__ == "__main__":
    filters = sys.argv[1:] or None
    if filters:
        print(_c(f"\nRunning tests matching: {', '.join(filters)}", YELLOW))
    else:
        print(_c("\nRunning all tests", BOLD))
    failed = run_all(filters)
    sys.exit(1 if failed else 0)
