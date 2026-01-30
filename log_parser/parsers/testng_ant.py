import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_testng_ant(log: str) -> dict[str, str]:
    results = {}
    pattern = re.compile(r"\[testng\]\s+(PASSED|FAILED|SKIPPED):\s+(.+)")
    for line in log.splitlines():
        match = pattern.search(line)
        if match:
            status_str, test_name = match.groups()
            results[test_name.strip()] = status_str.strip()
    return results
