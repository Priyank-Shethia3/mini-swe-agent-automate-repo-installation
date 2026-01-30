import re
import xml.etree.ElementTree as ET


def parse_log_bazel_custom(log: str) -> dict[str, str]:
    results = {}

    # Try parsing XML first
    xml_blocks = re.findall(r"<\?xml.*?</testsuite>", log, re.DOTALL)
    for xml_str in xml_blocks:
        try:
            root = ET.fromstring(xml_str)
            for testcase in root.findall(".//testcase"):
                name = f"{testcase.get('classname')}.{testcase.get('name')}"
                status = "PASSED"
                if testcase.find("failure") is not None:
                    status = "FAILED"
                elif testcase.find("skipped") is not None:
                    status = "SKIPPED"
                results[name] = status
        except Exception:
            continue

    # Fallback to summary line if no XML found or no cases extracted
    if not results:
        summary_match = re.search(
            r"//src/test/cpp/util:strings_test\s+(PASSED|FAILED)", log
        )
        if summary_match:
            results["//src/test/cpp/util:strings_test"] = summary_match.group(1)

    return results
