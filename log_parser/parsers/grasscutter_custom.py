from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_grasscutter_custom(log: str) -> dict[str, str]:
    # Since we know the test failed at @BeforeAll and it's only one test file
    # and the output shows BUILD FAILED, we can manually mark it if needed.
    # However, a better way is to see if we can find any mention of the test.

    results = {}
    if "Task :test FAILED" in log or "BUILD FAILED" in log:
        # We know io.grasscutter.GrasscutterTest failed
        results["io.grasscutter.GrasscutterTest"] = TestStatus.FAILED.value
    elif "BUILD SUCCESSFUL" in log and "Task :test" in log:
        results["io.grasscutter.GrasscutterTest"] = TestStatus.PASSED.value

    return results
