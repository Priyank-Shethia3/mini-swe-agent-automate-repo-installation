"""
CppUnit test log parser for C++.
"""

import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_cppunit(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with CppUnit.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for individual test failures
    # Example: "1) test: TestSuite::testMethod (F) line: 123 message"
    # Example: "Test name: TestSuite::testMethod"
    failure_pattern = r'(?:\d+\)|\*)\s*(?:test|Test)(?:\s+name)?:\s*([\w:]+(?:::[\w]+)*)'
    
    failed_tests = set()
    for match in re.finditer(failure_pattern, log):
        test_name = match.group(1)
        failed_tests.add(test_name)
        test_status_map[test_name] = TestStatus.FAILED.value

    # Check for failure indicators
    # "!!!FAILURES!!!" section typically lists failed tests
    if "!!!FAILURES!!!" in log:
        failures_section = log.split("!!!FAILURES!!!")[1] if "!!!" in log else ""
        # Extract test names from failures section
        for match in re.finditer(r'(?:Test name|test):\s*([\w:]+(?:::[\w]+)*)', failures_section):
            test_name = match.group(1)
            if test_name not in test_status_map:
                test_status_map[test_name] = TestStatus.FAILED.value

    # Look for success summary
    # "OK (150 tests)"
    # "Tests run: 150"
    ok_match = re.search(r'OK\s*\((\d+)\s+tests?\)', log, re.IGNORECASE)
    if ok_match:
        passed = int(ok_match.group(1))
        # All tests passed
        for i in range(passed):
            test_status_map[f"test_passed_{i+1}"] = TestStatus.PASSED.value
        return test_status_map

    # Alternative summary format
    # "Test Results:"
    # "Run: 150  Failures: 2  Errors: 0"
    summary_match = re.search(
        r'(?:Test Results:.*?)?Run:\s*(\d+)\s+Failures:\s*(\d+)\s+Errors:\s*(\d+)',
        log,
        re.DOTALL | re.IGNORECASE
    )
    if summary_match:
        total = int(summary_match.group(1))
        failures = int(summary_match.group(2))
        errors = int(summary_match.group(3))
        
        passed = total - failures - errors
        
        # If we don't have specific test names, create synthetic entries
        if not test_status_map:
            for i in range(passed):
                test_status_map[f"test_passed_{i+1}"] = TestStatus.PASSED.value
            for i in range(failures + errors):
                test_status_map[f"test_failed_{i+1}"] = TestStatus.FAILED.value
        else:
            # We have some specific failures, fill in the rest as passes
            specific_failures = len([v for v in test_status_map.values() if v == TestStatus.FAILED.value])
            remaining_passes = total - specific_failures
            for i in range(remaining_passes):
                test_status_map[f"test_passed_{i+1}"] = TestStatus.PASSED.value

        return test_status_map

    # If we found individual failures but no summary, assume those are the only tests
    if test_status_map:
        return test_status_map

    # Last fallback: Check if there's any indication of tests
    # "There were N failures:" or "There were N errors:"
    failure_count = re.search(r'There (?:were|was) (\d+) failures?', log, re.IGNORECASE)
    error_count = re.search(r'There (?:were|was) (\d+) errors?', log, re.IGNORECASE)
    
    if failure_count or error_count:
        failures = int(failure_count.group(1)) if failure_count else 0
        errors = int(error_count.group(1)) if error_count else 0
        
        for i in range(failures + errors):
            test_status_map[f"test_failed_{i+1}"] = TestStatus.FAILED.value

    return test_status_map
