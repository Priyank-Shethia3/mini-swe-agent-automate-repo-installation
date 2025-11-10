"""
Jest test log parser.
"""

import re
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED" 
    SKIPPED = "SKIPPED"

def parse_log_jest(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with Jest. Assumes --verbose flag.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for Jest verbose output with checkmarks/crosses
    pattern = r"^\s*(✓|✕|○)\s(.+?)(?:\s\((\d+\s*m?s)\))?$"

    for line in log.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            status_symbol, test_name, _duration = match.groups()
            if status_symbol == "✓":
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status_symbol == "✕":
                test_status_map[test_name] = TestStatus.FAILED.value
            elif status_symbol == "○":
                test_status_map[test_name] = TestStatus.SKIPPED.value

    # Alternative pattern for Jest summary format
    if not test_status_map:
        # Pattern for "PASS/FAIL filename" or "PASS/FAIL test description"
        summary_pattern = r"^\s*(PASS|FAIL|SKIP)\s+(.+?)(?:\s\((\d+\.\d+\s*s?)\))?$"
        for line in log.split("\n"):
            match = re.match(summary_pattern, line.strip())
            if match:
                status, test_name, _duration = match.groups()
                if status == "PASS":
                    test_status_map[test_name] = TestStatus.PASSED.value
                elif status == "FAIL":
                    test_status_map[test_name] = TestStatus.FAILED.value
                elif status == "SKIP":
                    test_status_map[test_name] = TestStatus.SKIPPED.value

    return test_status_map