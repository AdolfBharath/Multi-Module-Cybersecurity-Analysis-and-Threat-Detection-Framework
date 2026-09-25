import os
import sys

_total_tests = 0
_completed_tests = 0
_failed = False


def pytest_collection_modifyitems(session, config, items):  # noqa: ARG001
    global _total_tests
    _total_tests = len(items)


def pytest_runtest_logreport(report):
    global _completed_tests, _failed
    if report.when != "call":
        return
    _completed_tests += 1
    if report.failed:
        _failed = True
    if _total_tests and _completed_tests >= _total_tests:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1 if _failed else 0)
