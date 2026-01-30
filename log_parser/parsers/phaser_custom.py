from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_phaser_custom(log: str) -> dict[str, str]:
    results = {}
    if "=== Command 1: npm run tsgen ===" in log:
        parts = log.split("=== Command 1: npm run tsgen ===")
        if len(parts) > 1:
            segment = parts[1].split("=== Command")[0]
            results["tsgen"] = (
                TestStatus.PASSED.value
                if "Exit code: 0" in segment
                else TestStatus.FAILED.value
            )
    if "=== Command 2: npm run test-ts ===" in log:
        parts = log.split("=== Command 2: npm run test-ts ===")
        if len(parts) > 1:
            segment = parts[1]
            results["test-ts"] = (
                TestStatus.PASSED.value
                if "Exit code: 0" in segment
                else TestStatus.FAILED.value
            )
    return results
