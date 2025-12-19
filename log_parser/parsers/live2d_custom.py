from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

def parse_log_live2d_custom(log: str) -> dict[str, str]:
    results = {}
    if "eslint" in log:
        # If there are no errors mentioned in the output, it passed.
        # ESLint typical error output contains "error" or "problem"
        if "error" in log.lower() or "problem" in log.lower() or "Exit code: 2" in log or "Exit code: 1" in log:
            results["eslint_check"] = TestStatus.FAILED.value
        else:
            results["eslint_check"] = TestStatus.PASSED.value
    return results
