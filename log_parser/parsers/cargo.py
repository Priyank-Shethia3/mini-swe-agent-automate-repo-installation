"""
Cargo test log parser for Rust.
"""

import re
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED" 
    SKIPPED = "SKIPPED"

def parse_log_cargo(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with cargo test.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for cargo test output
    # Examples:
    # "test test_function ... ok"
    # "test test_function ... FAILED"
    # "test test_function ... ignored"
    
    test_pattern = r"^test\s+(\S+)\s+\.\.\.\s+(ok|FAILED|ignored)$"
    
    for line in log.split("\n"):
        line = line.strip()
        match = re.match(test_pattern, line)
        if match:
            test_name, status = match.groups()
            
            if status == "ok":
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status == "FAILED":
                test_status_map[test_name] = TestStatus.FAILED.value
            elif status == "ignored":
                test_status_map[test_name] = TestStatus.SKIPPED.value

    # Alternative pattern for doctests
    # "   Doc-tests project_name"
    # "test src/lib.rs - function_name (line X) ... ok"
    doctest_pattern = r"^test\s+\S+\s+-\s+(\w+)\s+.*\.\.\.\s+(ok|FAILED)$"
    
    for line in log.split("\n"):
        line = line.strip()
        match = re.match(doctest_pattern, line)
        if match:
            test_name, status = match.groups()
            test_name = f"doctest_{test_name}"
            
            if status == "ok":
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status == "FAILED":
                test_status_map[test_name] = TestStatus.FAILED.value

    return test_status_map