from enum import Enum
import re

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

def parse_log_plotly_custom(log: str) -> dict[str, str]:
    results = {}
    
    # Parse test-syntax results
    syntax_ok_patterns = [
        "ok no jasmine suites focus/exclude blocks or wrong tag patterns",
        "ok circular dependencies: 0",
        "ok correct headers and contents in lib/ and src/",
        "ok lower case only file names",
        "ok trailing new line character",
        "ok find_locale_strings - no output requested."
    ]
    for pattern in syntax_ok_patterns:
        if pattern in log:
            results[f"syntax: {pattern}"] = TestStatus.PASSED.value

    # Parse test-plain-obj
    if "{ data: [ { y: [Array] } ], layout: {} }" in log:
        results["test-plain-obj: output1"] = TestStatus.PASSED.value
    if "{ data: [ { z: false } ], layout: {} }" in log:
        results["test-plain-obj: output2"] = TestStatus.PASSED.value

    # Parse test-mock validations
    validating_matches = re.findall(r"validating ([\w-]+)", log)
    for mock_name in validating_matches:
        results[f"mock_validation: {mock_name}"] = TestStatus.PASSED.value

    return results
