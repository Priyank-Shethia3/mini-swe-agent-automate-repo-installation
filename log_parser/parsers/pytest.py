"""
Pytest test log parser.
"""

import re
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED" 
    SKIPPED = "SKIPPED"

def parse_log_pytest(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with pytest.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for pytest verbose output
    # Examples:
    # "test_file.py::test_function PASSED"
    # "test_file.py::TestClass::test_method FAILED"
    # "test_file.py::test_skip SKIPPED"
    
    verbose_pattern = r"^(.+?)::([\w_]+(?:::[\w_]+)?)\s+(PASSED|FAILED|SKIPPED|ERROR)(?:\s+\[.*?\])?$"
    
    for line in log.split("\n"):
        line = line.strip()
        match = re.match(verbose_pattern, line)
        if match:
            file_part, test_part, status = match.groups()
            
            # Create a readable test name
            if "::" in test_part:
                # Format: TestClass::test_method -> TestClass.test_method
                test_name = test_part.replace("::", ".")
            else:
                test_name = test_part
                
            if status in ["PASSED"]:
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status in ["FAILED", "ERROR"]:
                test_status_map[test_name] = TestStatus.FAILED.value
            elif status in ["SKIPPED"]:
                test_status_map[test_name] = TestStatus.SKIPPED.value

    # Alternative pattern for dot notation output
    if not test_status_map:
        # Look for short test summary info
        summary_pattern = r"^(FAILED|PASSED|SKIPPED)\s+(.+?)(?:\s+-\s+.*)?$"
        for line in log.split("\n"):
            match = re.match(summary_pattern, line.strip())
            if match:
                status, test_name = match.groups()
                if status == "PASSED":
                    test_status_map[test_name] = TestStatus.PASSED.value
                elif status == "FAILED":
                    test_status_map[test_name] = TestStatus.FAILED.value
                elif status == "SKIPPED":
                    test_status_map[test_name] = TestStatus.SKIPPED.value

    return test_status_map