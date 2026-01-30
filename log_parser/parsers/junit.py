"""
JUnit test log parser for Java (Ant-based builds).
Parses test output from Apache Ant JUnit task.
"""

import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_junit(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with JUnit via Apache Ant.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}
    current_class = None

    for line in log.split("\n"):
        line = line.strip()

        # Strip common Ant log prefixes like [test], [junit], etc.
        cleaned_line = re.sub(r"^\[[^\]]+\]\s+", "", line)

        # Track current test class
        # Example: "Running com.gitblit.StoredUserConfigTest"
        class_match = re.match(r"^Running\s+(.+)$", cleaned_line)
        if class_match:
            current_class = class_match.group(1)
            continue

        # Parse test summary lines (class-level)
        # Example: "Tests run: 7, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.173 sec"
        summary_match = re.match(
            r"^Tests run:\s+(\d+),\s+Failures:\s+(\d+),\s+Errors:\s+(\d+),\s+Skipped:\s+(\d+)",
            cleaned_line,
        )
        if summary_match:
            tests_run = int(summary_match.group(1))
            failures = int(summary_match.group(2))
            errors = int(summary_match.group(3))
            skipped = int(summary_match.group(4))

            if current_class:
                # Create entries for each test in the class
                # If we have failures/errors, mark them as failed
                # If we have skipped tests, create separate entries
                if failures > 0 or errors > 0:
                    for i in range(failures + errors):
                        test_status_map[f"{current_class}.test_{i + 1}"] = (
                            TestStatus.FAILED.value
                        )
                    # Add passed tests
                    for i in range(tests_run - failures - errors - skipped):
                        test_status_map[
                            f"{current_class}.test_{failures + errors + i + 1}"
                        ] = TestStatus.PASSED.value
                    # Add skipped tests
                    for i in range(skipped):
                        test_status_map[
                            f"{current_class}.test_{tests_run - skipped + i + 1}"
                        ] = TestStatus.SKIPPED.value
                else:
                    # All tests passed (minus skipped)
                    for i in range(tests_run - skipped):
                        test_status_map[f"{current_class}.test_{i + 1}"] = (
                            TestStatus.PASSED.value
                        )
                    # Add skipped tests
                    for i in range(skipped):
                        test_status_map[
                            f"{current_class}.test_{tests_run - skipped + i + 1}"
                        ] = TestStatus.SKIPPED.value
            continue

    # Alternative: Try to parse individual test method output if available
    # Some JUnit configurations output individual test results
    if not test_status_map:
        # Pattern for individual test methods with status
        # Example: "testMethodName(com.example.TestClass): FAILED"
        method_pattern = r"^(\w+)\(([^)]+)\):\s*(PASSED|FAILED|ERROR|SKIPPED)$"

        for line in log.split("\n"):
            cleaned_line = re.sub(r"^\[[^\]]+\]\s+", "", line.strip())

            match = re.match(method_pattern, cleaned_line)
            if match:
                method_name, class_name, status = match.groups()
                test_name = f"{class_name}.{method_name}"

                if status in ["FAILED", "ERROR"]:
                    test_status_map[test_name] = TestStatus.FAILED.value
                elif status == "SKIPPED":
                    test_status_map[test_name] = TestStatus.SKIPPED.value
                else:
                    test_status_map[test_name] = TestStatus.PASSED.value

    return test_status_map
