from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_stylelint(log: str) -> dict[str, str]:
    # Stylelint typically outputs errors to stdout/stderr.
    # If the process exited with 0 (which we know from the caller or by absence of errors),
    # and we see the command was executed, we can mark it as passed.
    if "stylelint" in log.lower():
        if "error" in log.lower() or "failed" in log.lower():
            return {"stylelint": TestStatus.FAILED.value}
        return {"stylelint": TestStatus.PASSED.value}
    return {}
