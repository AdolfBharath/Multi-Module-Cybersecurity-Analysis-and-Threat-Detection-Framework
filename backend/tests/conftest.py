import os
import sys

_total = 0
_seen = 0
_failed = False


def pytest_collection_modifyitems(session, config, items):
    global _total
    _total = len(items)


def pytest_runtest_logreport(report):
    global _seen, _failed
    if report.when != "call":
        return
    _seen += 1
    if report.failed:
        _failed = True
    if _total and _seen >= _total:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1 if _failed else 0)


def pytest_sessionfinish(session, exitstatus):
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exitstatus)
