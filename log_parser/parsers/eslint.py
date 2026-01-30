import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_eslint(log: str) -> dict[str, str]:
    """
    Parses ESLint output.
    Since ESLint doesn't always provide a clear "X tests passed" unless there are errors,
    we look for the absence of errors and the presence of the command execution.
    """
    results = {}

    # Check if there are any linting errors reported
    # ESLint output usually looks like:
    # /path/to/file.js
    #   1:1  error  'foo' is defined but never used  no-unused-vars
    # ✖ 1 problem (1 error, 0 warnings)

    error_match = re.search(r"✖ (\d+) problems? \((\d+) errors?", log)

    if error_match:
        error_count = int(error_match.group(2))
        if error_count > 0:
            results["eslint_check"] = TestStatus.FAILED.value
        else:
            # If problems found but 0 errors, it's just warnings
            results["eslint_check"] = TestStatus.PASSED.value
    elif "npm info ok" in log or "exit 0" in log:
        # If npm test exited with 0 and no error summary found, assume it passed
        results["eslint_check"] = TestStatus.PASSED.value

    return results
