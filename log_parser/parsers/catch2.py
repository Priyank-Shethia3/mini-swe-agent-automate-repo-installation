"""
Catch2 test log parser for C++.
"""

import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_catch2(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with Catch2.
    Supports both XML and text output formats.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Try XML format first (most common for CI)
    # Pattern: <TestCase name="Test Name" ...><OverallResult success="true|false"/>
    xml_pattern = r'<TestCase\s+name="([^"]+)"[^>]*>.*?<OverallResult\s+success="(true|false)"'
    
    for match in re.finditer(xml_pattern, log, re.DOTALL):
        test_name = match.group(1)
        success = match.group(2)
        
        if success == "true":
            test_status_map[test_name] = TestStatus.PASSED.value
        else:
            test_status_map[test_name] = TestStatus.FAILED.value

    # If XML parsing succeeded, return results
    if test_status_map:
        return test_status_map

    # Try text format
    # Pattern for test results in text mode:
    # "Test name" followed by result indicators
    # "All tests passed (123 assertions in 45 test cases)"
    # "test cases: 45 | 44 passed | 1 failed"

    # Look for individual test case results with pass/fail
    text_pattern = r'^([^:\n]+)\s+(?:PASSED|FAILED)'
    for line in log.split("\n"):
        line = line.strip()
        
        # Match lines like "TestName ... PASSED"
        if " PASSED" in line or "... PASSED" in line:
            test_name = line.replace(" PASSED", "").replace("... ", "").strip()
            if test_name:
                test_status_map[test_name] = TestStatus.PASSED.value
        elif " FAILED" in line or "... FAILED" in line:
            test_name = line.replace(" FAILED", "").replace("... ", "").strip()
            if test_name:
                test_status_map[test_name] = TestStatus.FAILED.value

    # If we found test results, return them
    if test_status_map:
        return test_status_map

    # Fallback: Parse summary line
    # "test cases: 150 | 149 passed | 1 failed"
    # "All tests passed (1234 assertions in 150 test cases)"
    summary_match = re.search(r'test cases:\s*(\d+)\s*\|\s*(\d+)\s*passed\s*\|\s*(\d+)\s*failed', log, re.IGNORECASE)
    if summary_match:
        total = int(summary_match.group(1))
        passed = int(summary_match.group(2))
        failed = int(summary_match.group(3))
        
        # Create synthetic test entries based on counts
        for i in range(passed):
            test_status_map[f"test_passed_{i+1}"] = TestStatus.PASSED.value
        for i in range(failed):
            test_status_map[f"test_failed_{i+1}"] = TestStatus.FAILED.value
        
        return test_status_map

    # Try "All tests passed" format
    all_passed = re.search(r'All tests passed\s*\(.*?(\d+)\s+test cases?\)', log, re.IGNORECASE)
    if all_passed:
        passed = int(all_passed.group(1))
        for i in range(passed):
            test_status_map[f"test_passed_{i+1}"] = TestStatus.PASSED.value

    return test_status_map
