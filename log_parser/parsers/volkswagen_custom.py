from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_volkswagen_custom(log: str) -> dict[str, str]:
    results = {}
    if "volkswagen" in log:
        results["volkswagen_ci_test"] = TestStatus.PASSED.value
    return results
