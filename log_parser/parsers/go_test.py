"""
Go test log parser.
"""

import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_go_test(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with Go test.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for Go test verbose output
    # Examples:
    # "=== RUN   TestFunction"
    # "--- PASS: TestFunction (0.00s)"
    # "--- FAIL: TestFunction (0.00s)"
    # "--- SKIP: TestFunction (0.00s)"

    result_pattern = r"^---\s+(PASS|FAIL|SKIP):\s+(\w+)(?:\s+\([\d\.]+s\))?.*$"

    for line in log.split("\n"):
        line = line.strip()
        match = re.match(result_pattern, line)
        if match:
            status, test_name = match.groups()

            if status == "PASS":
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status == "FAIL":
                test_status_map[test_name] = TestStatus.FAILED.value
            elif status == "SKIP":
                test_status_map[test_name] = TestStatus.SKIPPED.value

    # Alternative pattern for table tests or subtests
    # "    --- PASS: TestFunction/subtest (0.00s)"
    subtest_pattern = (
        r"^\s+---\s+(PASS|FAIL|SKIP):\s+(\w+/[\w/]+)(?:\s+\([\d\.]+s\))?.*$"
    )

    for line in log.split("\n"):
        line_stripped = line.strip()
        match = re.match(subtest_pattern, line)
        if match:
            status, test_name = match.groups()
            # Clean up the subtest name
            test_name = test_name.replace("/", ".")

            if status == "PASS":
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status == "FAIL":
                test_status_map[test_name] = TestStatus.FAILED.value
            elif status == "SKIP":
                test_status_map[test_name] = TestStatus.SKIPPED.value

    return test_status_map
