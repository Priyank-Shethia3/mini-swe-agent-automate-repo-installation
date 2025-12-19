import re
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

def parse_log_mocha_empty(log: str) -> dict[str, str]:
    """
    Parses Mocha logs, including cases where 0 tests pass.
    """
    results = {}
    
    # Standard Mocha "passing" line: "  13 passing (175ms)"
    passing_match = re.search(r'(\d+)\s+passing', log)
    if passing_match:
        count = int(passing_match.group(1))
        for i in range(count):
            results[f"passing_test_{i}"] = TestStatus.PASSED.value
            
    # Standard Mocha "failing" line: "  5 failing"
    failing_match = re.search(r'(\d+)\s+failing', log)
    if failing_match:
        count = int(failing_match.group(1))
        for i in range(count):
            results[f"failing_test_{i}"] = TestStatus.FAILED.value

    # If we explicitly see "0 passing" and no failing, it's valid
    if not results and "0 passing" in log:
        results["no_tests_found"] = TestStatus.PASSED.value

    return results
