import re
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

def parse_log_ctest(log: str) -> dict[str, str]:
    results = {}
    # Pattern for CTest output: " 47/70 Test #47: brpc_load_balancer_unittest .................   Passed  173.42 sec"
    ctest_pattern = re.compile(r'\s*\d+/\d+\s+Test\s+#\d+:\s+([\w\-/.]+)\s+\.+\s+(Passed|Failed)', re.IGNORECASE)
    for match in ctest_pattern.finditer(log):
        test_name = match.group(1)
        status = "PASSED" if match.group(2).lower() == "passed" else "FAILED"
        results[test_name] = status
    
    # Fallback/complement: "The following tests FAILED:" section
    failed_section = re.search(r'The following tests FAILED:\n((?:\s+\d+\s+-\s+[\w\-/.]+.*\n?)+)', log)
    if failed_section:
        for line in failed_section.group(1).splitlines():
            m = re.search(r'\d+\s+-\s+([\w\-/.]+)', line)
            if m:
                results[m.group(1)] = "FAILED"
    
    # If no individual tests found, try summary
    if not results:
        summary_match = re.search(r'(\d+)%\s+tests\s+passed,\s+(\d+)\s+tests\s+failed\s+out\s+of\s+(\d+)', log, re.IGNORECASE)
        if summary_match:
            total = int(summary_match.group(3))
            failed = int(summary_match.group(2))
            for i in range(total - failed):
                results[f"synthetic_pass_{i}"] = "PASSED"
            for i in range(failed):
                results[f"synthetic_fail_{i}"] = "FAILED"
                
    return results
