import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_ospec(log: str) -> dict[str, str]:
    """
    Parses ospec test output.
    Example: "All 1132053 assertions passed" or "100 assertions failed"
    """
    results = {}

    # Check for "All X assertions passed"
    pass_match = re.search(r"All (\d+) assertions passed", log)
    if pass_match:
        count = int(pass_match.group(1))
        # Since ospec doesn't list individual test names in summary, we create a aggregate entry
        results["all_assertions"] = TestStatus.PASSED.value
        return results

    # Check for failures
    # Example: "1 assertions failed"
    fail_match = re.search(r"(\d+) assertions failed", log)
    if fail_match:
        results["assertions_failed"] = TestStatus.FAILED.value

    return results
