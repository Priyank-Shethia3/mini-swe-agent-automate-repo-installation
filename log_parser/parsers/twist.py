import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_twist(log: str) -> dict[str, str]:
    test_status_map = {}

    passed_count = 0
    failed_count = 0
    skipped_count = 0

    # Remove ANSI escape sequences and other problematic characters
    clean_log = re.sub(r"\x1b\[[0-9;]*[mGJKHFH]", "", log)
    # Also handle the manual [2J [3J [H seen in the output
    clean_log = re.sub(r"\[2J \[3J \[H", "", clean_log)

    summary_line_pattern = r"Tests:\s+(\d+)\s+passed(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+skipped)?(?:,\s+(\d+)\s+total)?"

    for line in clean_log.split("\n"):
        match = re.search(summary_line_pattern, line)
        if match:
            passed_count = int(match.group(1)) if match.group(1) else 0
            failed_count = int(match.group(2)) if match.group(2) else 0
            skipped_count = int(match.group(3)) if match.group(3) else 0

    if passed_count > 0:
        for i in range(passed_count):
            test_status_map[f"twist_passed_{i + 1}"] = TestStatus.PASSED.value
    if failed_count > 0:
        for i in range(failed_count):
            test_status_map[f"twist_failed_{i + 1}"] = TestStatus.FAILED.value
    if skipped_count > 0:
        for i in range(skipped_count):
            test_status_map[f"twist_skipped_{i + 1}"] = TestStatus.SKIPPED.value

    return test_status_map
