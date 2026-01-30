import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def parse_log_jooq_custom(log: str) -> dict[str, str]:
    results = {}
    # Pattern for Maven surefire output: [INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.531 s -- in org.jooq.test.util.ConvertTest
    pattern = re.compile(
        r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+), Time elapsed: .* -- in ([\w\.]+)"
    )

    for line in log.splitlines():
        match = pattern.search(line)
        if match:
            run, fail, err, skip, name = match.groups()
            status = TestStatus.PASSED.value
            if int(fail) > 0 or int(err) > 0:
                status = TestStatus.FAILED.value
            elif int(skip) == int(run) and int(run) > 0:
                status = TestStatus.SKIPPED.value
            results[name] = status

    return results
