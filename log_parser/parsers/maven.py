"""
Maven/Gradle test log parser for Java.
"""

import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_maven(log: str) -> dict[str, str]:
    """
    Parser for test logs generated with Maven or Gradle.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}

    # Pattern for Maven Surefire output
    # Examples:
    # "Running com.example.TestClass"
    # "Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.123 sec"

    # First, look for individual test methods in verbose output
    # "testMethodName(com.example.TestClass)  Time elapsed: 0.001 sec"
    # "testMethodName(com.example.TestClass)  Time elapsed: 0.001 sec  <<< FAILURE!"
    method_pattern = r"^(\w+)\([^)]+\)\s+Time elapsed:.*?(?:<<<\s+(FAILURE|ERROR)!)?$"

    current_class = None

    for line in log.split("\n"):
        line = line.strip()

        # Strip common Maven log prefixes like [INFO], [DEBUG], [WARNING], [ERROR]
        cleaned_line = re.sub(r"^\[(INFO|DEBUG|WARNING|ERROR)\]\s+", "", line)

        # Track current test class
        class_match = re.match(r"^Running\s+(.+)$", cleaned_line)
        if class_match:
            current_class = class_match.group(1)
            continue

        # Parse test summary lines (class-level)
        # Example: "Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.416 s -- in io.github.classgraph.features.EnumTest"
        summary_match = re.match(
            r"^Tests run:\s+(\d+),\s+Failures:\s+(\d+),\s+Errors:\s+(\d+),\s+Skipped:\s+(\d+).*?(?:--\s+in\s+(.+))?$",
            cleaned_line,
        )
        if summary_match:
            tests_run = int(summary_match.group(1))
            failures = int(summary_match.group(2))
            errors = int(summary_match.group(3))
            skipped = int(summary_match.group(4))
            test_class = (
                summary_match.group(5) if summary_match.group(5) else current_class
            )

            if test_class:
                # Create entries for each test in the class
                # If we have failures/errors, mark the class as failed
                # If we have skipped tests, create separate entries
                if failures > 0 or errors > 0:
                    for i in range(failures + errors):
                        test_status_map[f"{test_class}.test_{i + 1}"] = (
                            TestStatus.FAILED.value
                        )
                    # Add passed tests
                    for i in range(tests_run - failures - errors - skipped):
                        test_status_map[
                            f"{test_class}.test_{failures + errors + i + 1}"
                        ] = TestStatus.PASSED.value
                    # Add skipped tests
                    for i in range(skipped):
                        test_status_map[
                            f"{test_class}.test_{tests_run - skipped + i + 1}"
                        ] = TestStatus.SKIPPED.value
                else:
                    # All tests passed (minus skipped)
                    for i in range(tests_run - skipped):
                        test_status_map[f"{test_class}.test_{i + 1}"] = (
                            TestStatus.PASSED.value
                        )
                    # Add skipped tests
                    for i in range(skipped):
                        test_status_map[
                            f"{test_class}.test_{tests_run - skipped + i + 1}"
                        ] = TestStatus.SKIPPED.value
            continue

        # Parse individual test methods (if available in verbose output)
        method_match = re.match(method_pattern, cleaned_line)
        if method_match:
            method_name = method_match.group(1)
            failure_indicator = method_match.group(2)

            test_name = (
                f"{current_class}.{method_name}" if current_class else method_name
            )

            if failure_indicator:
                test_status_map[test_name] = TestStatus.FAILED.value
            else:
                test_status_map[test_name] = TestStatus.PASSED.value

    # Alternative pattern for JUnit-style output
    if not test_status_map:
        # Look for JUnit XML-style patterns in console output
        junit_pattern = r"^\s*(PASS|FAIL|SKIP).*?(\w+\.\w+).*$"
        for line in log.split("\n"):
            match = re.match(junit_pattern, line.strip())
            if match:
                status, test_name = match.groups()
                if status == "PASS":
                    test_status_map[test_name] = TestStatus.PASSED.value
                elif status == "FAIL":
                    test_status_map[test_name] = TestStatus.FAILED.value
                elif status == "SKIP":
                    test_status_map[test_name] = TestStatus.SKIPPED.value

    # Gradle test output pattern
    if not test_status_map:
        # "com.example.TestClass > testMethod PASSED"
        gradle_pattern = r"^(.+?)\s+>\s+(\w+)\s+(PASSED|FAILED|SKIPPED)$"
        for line in log.split("\n"):
            match = re.match(gradle_pattern, line.strip())
            if match:
                class_name, method_name, status = match.groups()
                test_name = f"{class_name}.{method_name}"

                if status == "PASSED":
                    test_status_map[test_name] = TestStatus.PASSED.value
                elif status == "FAILED":
                    test_status_map[test_name] = TestStatus.FAILED.value
                elif status == "SKIPPED":
                    test_status_map[test_name] = TestStatus.SKIPPED.value

    return test_status_map
