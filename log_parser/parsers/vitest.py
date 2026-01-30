import re
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def parse_log_vitest(log: str) -> dict[str, str]:
    results = {}
    log = strip_ansi(log)
    file_summary_pattern = re.compile(
        r"([✓✗])\s+(.*?)\s+\((\d+)\s+tests?(?:\s+\|\s+(\d+)\s+skipped)?\)\s+\d+\s*ms"
    )
    for match in file_summary_pattern.finditer(log):
        status_char, file_path, test_count, skipped_count = match.groups()
        test_count = int(test_count)
        skipped_count = int(skipped_count or 0)
        status = (
            TestStatus.PASSED.value if status_char == "✓" else TestStatus.FAILED.value
        )
        for i in range(test_count - skipped_count):
            results[f"{file_path.strip()}_test_{i}"] = status
        for i in range(skipped_count):
            results[f"{file_path.strip()}_skipped_{i}"] = TestStatus.SKIPPED.value
    individual_test_pattern = re.compile(
        r"^\s+([✓✗])\s+(.*?)(?:\s+\d+\s+ms)?$", re.MULTILINE
    )
    for match in individual_test_pattern.finditer(log):
        status_char, test_name = match.groups()
        if "(" in test_name and "tests)" in test_name:
            continue
        status = (
            TestStatus.PASSED.value if status_char == "✓" else TestStatus.FAILED.value
        )
        results[f"individual_{test_name.strip()}_{len(results)}"] = status
    summary_match = re.search(
        r"Tests\s+(?:(\d+)\s+failed\s+\|)?\s*(?:(\d+)\s+passed\s+)?", log
    )
    if summary_match:
        failed = int(summary_match.group(1) or 0)
        passed = int(summary_match.group(2) or 0)
        if len(results) < (passed + failed) * 0.5:
            results = {}
            for i in range(passed):
                results[f"vitest_summary_passed_{i}"] = TestStatus.PASSED.value
            for i in range(failed):
                results[f"vitest_summary_failed_{i}"] = TestStatus.FAILED.value
    return results
