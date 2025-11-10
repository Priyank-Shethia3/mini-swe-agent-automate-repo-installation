"""
Mocha test log parser.
"""

import re
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED" 
    SKIPPED = "SKIPPED"

def parse_log_mocha(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with Mocha.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for Mocha spec reporter format
    # Examples:
    # "    ✓ should do something (42ms)"
    # "    1) should fail something"
    # "    - should skip something"
    
    for line in log.split("\n"):
        line = line.strip()
        
        # Passing tests (support both ✓ and ✔ checkmarks)
        pass_match = re.match(r"^\s*[✓✔]\s+(.+?)(?:\s+\((\d+\s*m?s)\))?$", line)
        if pass_match:
            test_name = pass_match.group(1).strip()
            test_status_map[test_name] = TestStatus.PASSED.value
            continue
            
        # Failing tests - pattern like "1) test name"
        fail_match = re.match(r"^\s*\d+\)\s+(.+)$", line)
        if fail_match:
            test_name = fail_match.group(1).strip()
            test_status_map[test_name] = TestStatus.FAILED.value
            continue
            
        # Skipped tests
        skip_match = re.match(r"^\s*-\s+(.+)$", line)
        if skip_match:
            test_name = skip_match.group(1).strip()
            test_status_map[test_name] = TestStatus.SKIPPED.value
            continue

    # Alternative pattern for TAP output from Mocha
    if not test_status_map:
        tap_pattern = r"^(ok|not ok)\s+\d+\s+(.+)$"
        for line in log.split("\n"):
            match = re.match(tap_pattern, line.strip())
            if match:
                status, test_name = match.groups()
                if status == "ok":
                    test_status_map[test_name] = TestStatus.PASSED.value
                else:
                    test_status_map[test_name] = TestStatus.FAILED.value

    return test_status_map