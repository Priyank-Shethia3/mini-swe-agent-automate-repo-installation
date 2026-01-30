from enum import Enum
import re


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_modernizr_custom(log: str) -> dict[str, str]:
    results = {}

    # Clean ANSI escape codes
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    log = ansi_escape.sub("", log)

    # Patterns for passing/failing tests in Mocha 'dot' reporter or summarized output
    # Example: "172 passing (2s)"
    passing_match = re.search(r"(\d+) passing", log)
    if passing_match:
        passing_count = int(passing_match.group(1))
        for i in range(passing_count):
            results[f"passed_test_{i}"] = TestStatus.PASSED.value

    # Look for failures
    # Example: "1 failing" or list of failures
    failing_match = re.search(r"(\d+) failing", log)
    if failing_match:
        failing_count = int(failing_match.group(1))
        for i in range(failing_count):
            results[f"failed_test_{i}"] = TestStatus.FAILED.value

    # Handle the specific failure seen in logs if it didn't match the summary
    if "DOMException: SyntaxError" in log and not results:
        results["DOMException_Failure"] = TestStatus.FAILED.value

    return results
