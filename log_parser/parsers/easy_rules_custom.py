import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_easy_rules_custom(log: str) -> dict[str, str]:
    results = {}
    # Pattern to match: [INFO] Tests run: 113, Failures: 0, Errors: 0, Skipped: 0
    pattern = r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)"
    matches = re.finditer(pattern, log)

    total_tests = 0
    total_failed = 0
    total_skipped = 0

    found = False
    for match in matches:
        found = True
        run, fail, err, skip = map(int, match.groups())
        total_tests += run
        total_failed += fail + err
        total_skipped += skip

    if not found:
        return {}

    # Since we don't have individual test names easily, we'll create aggregate entries
    for i in range(total_tests - total_failed - total_skipped):
        results[f"test_pass_{i}"] = TestStatus.PASSED.value
    for i in range(total_failed):
        results[f"test_fail_{i}"] = TestStatus.FAILED.value
    for i in range(total_skipped):
        results[f"test_skip_{i}"] = TestStatus.SKIPPED.value

    return results
