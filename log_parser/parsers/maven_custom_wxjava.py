import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_maven_custom_wxjava(log: str) -> dict[str, str]:
    results = {}
    # Pattern for Surefire plain format: Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.001 s - in me.chanjar.weixin.common.util.ToStringUtilsTest
    pattern = re.compile(
        r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+),.* - in ([\w\.]+)"
    )

    for line in log.splitlines():
        match = pattern.search(line)
        if match:
            total = int(match.group(1))
            fail = int(match.group(2))
            error = int(match.group(3))
            skipped = int(match.group(4))
            test_class = match.group(5)

            # We don't have individual test names in this summary line,
            # so we use the class name as a proxy for the suite
            if fail > 0 or error > 0:
                results[test_class] = TestStatus.FAILED.value
            elif skipped == total:
                results[test_class] = TestStatus.SKIPPED.value
            else:
                results[test_class] = TestStatus.PASSED.value

    return results
