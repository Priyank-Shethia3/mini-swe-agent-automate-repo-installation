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

    # Check Jest summary line and supplement if needed
    # Pattern: "Tests:       1992 passed, 1992 total"
    summary_line_pattern = r"Tests:\s+(\d+)\s+passed(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+skipped)?(?:,\s+(\d+)\s+total)?"
    
    for line in log.split("\n"):
        match = re.search(summary_line_pattern, line)
        if match:
            passed_count = int(match.group(1)) if match.group(1) else 0
            failed_count = int(match.group(2)) if match.group(2) else 0
            skipped_count = int(match.group(3)) if match.group(3) else 0
            
            # Count what we've already parsed
            parsed_passed = sum(1 for status in test_status_map.values() if status == TestStatus.PASSED.value)
            parsed_failed = sum(1 for status in test_status_map.values() if status == TestStatus.FAILED.value)
            parsed_skipped = sum(1 for status in test_status_map.values() if status == TestStatus.SKIPPED.value)
            
            # Supplement with generic entries for missing tests
            missing_passed = passed_count - parsed_passed
            missing_failed = failed_count - parsed_failed
            missing_skipped = skipped_count - parsed_skipped
            
            if missing_passed > 0:
                for i in range(missing_passed):
                    test_status_map[f"jest_test_{i+1}"] = TestStatus.PASSED.value
            
            if missing_failed > 0:
                for i in range(missing_failed):
                    test_status_map[f"jest_failed_test_{i+1}"] = TestStatus.FAILED.value
            
            if missing_skipped > 0:
                for i in range(missing_skipped):
                    test_status_map[f"jest_skipped_test_{i+1}"] = TestStatus.SKIPPED.value
            
            break  # Only process first summary line

    return test_status_map