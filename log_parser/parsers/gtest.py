"""
Google Test (gtest) log parser for C++.
"""

import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_gtest(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with Google Test.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}
    current_test = None

    # Pattern for individual test results
    # Examples:
    # "[       OK ] TestSuite.TestName (123 ms)"
    # "[  FAILED  ] TestSuite.TestName (456 ms)"
    # "[ RUN      ] TestSuite.TestName"
    # "[  PASSED  ] 150 tests."
    # "[  SKIPPED ] TestSuite.TestName"

    for line in log.split("\n"):
        line = line.strip()

        # Match RUN lines to capture test name
        run_match = re.match(r'\[\s*RUN\s*\]\s+([\w:/.]+)', line)
        if run_match:
            current_test = run_match.group(1)
            continue

        # Match OK/PASSED result lines
        ok_match = re.match(r'\[\s*(OK|PASSED)\s*\]\s+([\w:/.]+)', line)
        if ok_match:
            test_name = ok_match.group(2)
            test_status_map[test_name] = TestStatus.PASSED.value
            current_test = None
            continue

        # Match FAILED result lines (but not summary lines with "tests")
        failed_match = re.match(r'\[\s*FAILED\s*\]\s+([\w:/.]+)(?:\s+\(|$)', line)
        if failed_match:
            test_name = failed_match.group(1)
            # Avoid matching summary lines like "[  FAILED  ] 2 tests"
            if not test_name.isdigit():
                test_status_map[test_name] = TestStatus.FAILED.value
            current_test = None
            continue

        # Match SKIPPED/DISABLED result lines
        skip_match = re.match(r'\[\s*(SKIPPED|DISABLED)\s*\]\s+([\w:/.]+)', line)
        if skip_match:
            test_name = skip_match.group(2)
            test_status_map[test_name] = TestStatus.SKIPPED.value
            current_test = None
            continue

    # Fallback: Try to parse summary lines if no individual tests found
    if test_status_map:
        return test_status_map
    # "[==========] 150 tests from 25 test suites ran."
    # "[  PASSED  ] 149 tests."
    # "[  FAILED  ] 1 test, listed below:"
    summary_tests = re.search(r'\[\s*=+\s*\]\s*(\d+)\s+tests?\s+from', log)
    summary_passed = re.search(r'\[\s*PASSED\s*\]\s*(\d+)\s+tests?', log)
    summary_failed = re.search(r'\[\s*FAILED\s*\]\s*(\d+)\s+tests?', log)

    if summary_tests:
        total_tests = int(summary_tests.group(1))
        passed_tests = int(summary_passed.group(1)) if summary_passed else 0
        failed_tests = int(summary_failed.group(1)) if summary_failed else 0

        # Create synthetic test entries
        for i in range(passed_tests):
            test_status_map[f"test_passed_{i+1}"] = TestStatus.PASSED.value
        for i in range(failed_tests):
            test_status_map[f"test_failed_{i+1}"] = TestStatus.FAILED.value

    return test_status_map
