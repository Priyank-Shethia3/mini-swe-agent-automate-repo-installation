"""
Boost.Test log parser for C++.
"""

import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_boost_test(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with Boost.Test.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for individual test failures
    # Example: "error: in "test_suite/test_case_name": check x == y has failed"
    # Example: "error in "test_suite/test_case_name": some error message"
    failure_pattern = r'error(?:\s+in)?\s+"([^"]+)"'
    
    failed_tests = set()
    for match in re.finditer(failure_pattern, log, re.IGNORECASE):
        test_name = match.group(1)
        failed_tests.add(test_name)
        test_status_map[test_name] = TestStatus.FAILED.value

    # Pattern for entering/leaving test cases (to find all tests)
    # "Entering test case "test_name""
    # "Leaving test case "test_name""
    entering_pattern = r'Entering test (?:case|suite) "([^"]+)"'
    
    all_tests = set()
    for match in re.finditer(entering_pattern, log):
        test_name = match.group(1)
        all_tests.add(test_name)

    # Mark all tests that weren't marked as failed as passed
    for test_name in all_tests:
        if test_name not in failed_tests:
            test_status_map[test_name] = TestStatus.PASSED.value

    # If we found individual tests, return them
    if test_status_map:
        return test_status_map

    # Fallback: Check for summary indicators
    # "*** No errors detected" means all tests passed
    if re.search(r'\*\*\* No errors detected', log):
        # Try to extract test count from summary
        # "Test case ... passed"
        # "N test cases passed"
        test_count_match = re.search(r'(\d+)\s+test cases?\s+(?:out of \d+ )?passed', log, re.IGNORECASE)
        if test_count_match:
            passed = int(test_count_match.group(1))
            for i in range(passed):
                test_status_map[f"test_passed_{i+1}"] = TestStatus.PASSED.value
        elif not test_status_map:
            # If we see "No errors detected" but no count, mark as at least one passing test
            test_status_map["boost_test_suite"] = TestStatus.PASSED.value
        return test_status_map

    # Check for failure summary
    # "*** N failure(s) detected"
    failure_summary = re.search(r'\*\*\* (\d+) failure(?:s)? detected', log)
    if failure_summary:
        failures = int(failure_summary.group(1))
        
        # If we already have specific failed tests from earlier parsing
        if len([v for v in test_status_map.values() if v == TestStatus.FAILED.value]) == 0:
            # Create synthetic failure entries
            for i in range(failures):
                test_status_map[f"test_failed_{i+1}"] = TestStatus.FAILED.value

    return test_status_map
